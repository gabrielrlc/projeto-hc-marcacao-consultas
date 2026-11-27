"""
Controller de Importação e Higienização ``Forms × AGHU`` (TASK-007 / RF003 / UC002)
===================================================================================
Cruza cada linha da planilha do Google Forms com a base somente-leitura do AGHU
(via ``ExameProviderInterface``) e grava o resultado em ``acompanhamento_fila``.

Classificação (``status_higienizacao``) de cada linha/item, nesta ordem:

1. ``NAO_ENCONTRADA`` — número da solicitação vazio, inexistente no AGHU, ou
   pertencente a **outro prontuário** (o paciente digitou o número errado). A
   marcadora resolve via busca ativa por prontuário.
2. ``DIVERGENCIA_EXAME`` — o exame informado no Forms não corresponde a nenhum
   item da solicitação no AGHU (os exames reais vão em ``observacoes``).
3. ``JA_REALIZADA`` — linha pintada de verde no XLSX (convenção da Central para
   "agendado"), ou item já ``CONFIRMADO_AGENDADO_AGHU`` na fila.
4. ``DUPLICADA`` — mesmo ``(solicitação, exame)`` ou mesmo ``(prontuário, exame)``
   (vários médicos pedindo o mesmo exame) já presente na planilha ou ativo na fila.
5. ``VALIDA`` — demais casos; entra na fila de marcação.

Uma linha do Forms pode gerar vários itens quando o exame informado corresponde
a mais de um exame da solicitação (ou quando o exame não foi informado). As
linhas são processadas em ordem cronológica (carimbo do Forms) para que o
primeiro envio seja o válido e os reenvios fiquem como duplicados.

Todos os itens (válidos e exceções) são persistidos para revisão; a fila deve
listar apenas ``status_higienizacao = 'VALIDA'``.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..helpers.audit_helper import registrar_auditoria
from ..helpers.exame_match_helper import exame_corresponde
from ..helpers.geografia_helper import classificar_regiao
from ..helpers.planilha_forms_helper import LinhaForms, ResultadoLeituraPlanilha
from ..helpers.string_helper import somente_digitos, texto_ou_none
from ..models import AcompanhamentoFila, ImportacaoForms, STATUS_HIGIENIZACAO_VALIDOS
from ..providers.interfaces.exame_provider_interface import ExameProviderInterface

CATEGORIA_AUDITORIA = "NEGOCIO_CLINICO"
NOME_NAO_INFORMADO = "NÃO INFORMADO"
CODIGO_NAO_INFORMADO = "NAO_INFORMADO"


@dataclass
class ItemHigienizado:
    """Resultado da higienização de um item (linha do Forms × exame do AGHU)."""

    linha: LinhaForms
    status_higienizacao: str
    codigo_solicitacao: str
    codigo_exame: Optional[str]
    prontuario: Optional[str]
    nome_paciente: str
    telefone_contato: Optional[str]
    municipio: Optional[str]
    unidade_solicitante: Optional[str]
    especialidade_solicitante: Optional[str]
    observacoes: Optional[str] = None


@dataclass(frozen=True)
class RegistroFilaExistente:
    """Item ativo já presente na fila, usado na detecção de duplicidades."""

    id: int
    codigo_solicitacao: str
    codigo_exame: Optional[str]
    prontuario: Optional[str]
    status_operacional: str


# ---------------------------------------------------------------------------
# Classificação (função pura, sem I/O)
# ---------------------------------------------------------------------------


def _chave_ordenacao(linha: LinhaForms) -> Tuple[int, datetime, int]:
    """Ordena por carimbo do Forms (sem carimbo ao final), preservando a ordem do arquivo."""
    return (0 if linha.carimbo else 1, linha.carimbo or datetime.min, linha.numero_linha)


def _item_base(linha: LinhaForms, codigo: str, aghu: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Monta os dados do item, priorizando o AGHU para identificação e o Forms para contato."""
    aghu = aghu or {}
    return {
        "linha": linha,
        "codigo_solicitacao": codigo,
        "codigo_exame": texto_ou_none(aghu.get("codigo_exame")),
        "prontuario": texto_ou_none(aghu.get("prontuario")) or texto_ou_none(linha.prontuario),
        "nome_paciente": texto_ou_none(aghu.get("nome")) or linha.nome_paciente or NOME_NAO_INFORMADO,
        "telefone_contato": linha.telefone or texto_ou_none(aghu.get("telefone")),
        "municipio": linha.municipio or texto_ou_none(aghu.get("cidade")),
        "unidade_solicitante": texto_ou_none(aghu.get("unidade_solicitante")),
        "especialidade_solicitante": texto_ou_none(aghu.get("especialidade_solicitante")),
    }


def _descrever_exames(itens: Iterable[Dict[str, Any]]) -> str:
    """Lista os exames de uma solicitação no AGHU para exibição em ``observacoes``."""
    return "; ".join(f"{i.get('codigo_exame')} ({i.get('nome_exame')})" for i in itens)


def classificar_linhas(
    linhas: List[LinhaForms],
    aghu_por_solicitacao: Dict[str, List[Dict[str, Any]]],
    fila_existente: Iterable[RegistroFilaExistente] = (),
) -> List[ItemHigienizado]:
    """
    Classifica as linhas do Forms contra o AGHU e a fila já existente.

    Args:
        linhas: Linhas lidas da planilha do Forms.
        aghu_por_solicitacao: Itens do AGHU indexados pelo número da solicitação (só dígitos).
        fila_existente: Itens ativos (``VALIDA``, não cancelados) já presentes na fila.

    Returns:
        Itens higienizados na ordem cronológica de processamento.
    """
    por_solicitacao: Dict[Tuple[str, str], RegistroFilaExistente] = {}
    por_prontuario: Dict[Tuple[str, str], RegistroFilaExistente] = {}
    for registro in fila_existente:
        if not registro.codigo_exame:
            continue
        por_solicitacao.setdefault((registro.codigo_solicitacao, registro.codigo_exame), registro)
        if registro.prontuario:
            por_prontuario.setdefault((somente_digitos(registro.prontuario), registro.codigo_exame), registro)

    vistos_solicitacao: Dict[Tuple[str, str], int] = {}
    vistos_prontuario: Dict[Tuple[str, str], int] = {}
    resultado: List[ItemHigienizado] = []

    for linha in sorted(linhas, key=_chave_ordenacao):
        codigo = somente_digitos(linha.codigo_solicitacao_bruto)
        codigo_exibicao = codigo or (linha.codigo_solicitacao_bruto or CODIGO_NAO_INFORMADO)[:64]
        itens_aghu = aghu_por_solicitacao.get(codigo, []) if codigo else []

        # 1. Solicitação inexistente / vazia
        if not itens_aghu:
            motivo = (
                "Número da solicitação não informado."
                if not codigo
                else "Solicitação não encontrada no AGHU. Utilize a busca ativa por prontuário."
            )
            resultado.append(ItemHigienizado(
                **_item_base(linha, codigo_exibicao, None), status_higienizacao="NAO_ENCONTRADA", observacoes=motivo,
            ))
            continue

        # 1b. Solicitação existente, mas de outro paciente (número digitado errado)
        prontuario_forms = somente_digitos(linha.prontuario)
        prontuario_aghu = somente_digitos(itens_aghu[0].get("prontuario"))
        if prontuario_forms and prontuario_aghu and prontuario_forms != prontuario_aghu:
            item = _item_base(linha, codigo, None)
            item["prontuario"] = linha.prontuario
            resultado.append(ItemHigienizado(
                **item,
                status_higienizacao="NAO_ENCONTRADA",
                observacoes=(
                    f"A solicitação {codigo} pertence a outro prontuário no AGHU. "
                    "Verifique o número informado e utilize a busca ativa por prontuário."
                ),
            ))
            continue

        # 2. Correspondência do exame informado
        if linha.exame_informado:
            correspondentes = [i for i in itens_aghu if exame_corresponde(linha.exame_informado, i)]
        else:
            correspondentes = list(itens_aghu)

        if not correspondentes:
            item = _item_base(linha, codigo, itens_aghu[0])
            item["codigo_exame"] = None
            resultado.append(ItemHigienizado(
                **item,
                status_higienizacao="DIVERGENCIA_EXAME",
                observacoes=(
                    f"Exame informado no Forms ('{linha.exame_informado}') não corresponde ao pedido médico. "
                    f"Exames da solicitação no AGHU: {_descrever_exames(itens_aghu)}."
                ),
            ))
            continue

        for aghu in correspondentes:
            item = _item_base(linha, codigo, aghu)
            exame = item["codigo_exame"]
            chave_sol = (codigo, exame)
            chave_pront = (somente_digitos(item["prontuario"]), exame) if item["prontuario"] else None
            existente = por_solicitacao.get(chave_sol) or (por_prontuario.get(chave_pront) if chave_pront else None)

            # 3. Já agendado/realizado
            if linha.marcada_agendada:
                status_item, obs = "JA_REALIZADA", "Linha marcada como agendada (verde) na planilha do Forms."
            elif existente and existente.status_operacional == "CONFIRMADO_AGENDADO_AGHU":
                status_item, obs = "JA_REALIZADA", f"Exame já confirmado/agendado no AGHU (item #{existente.id} da fila)."
            # 4. Duplicidades
            elif chave_sol in vistos_solicitacao:
                status_item, obs = "DUPLICADA", f"Envio repetido da mesma solicitação (linha {vistos_solicitacao[chave_sol]} da planilha)."
            elif chave_pront and chave_pront in vistos_prontuario:
                status_item, obs = "DUPLICADA", (
                    f"Mesmo exame ({exame}) solicitado mais de uma vez para o prontuário "
                    f"(linha {vistos_prontuario[chave_pront]} da planilha)."
                )
            elif existente:
                status_item, obs = "DUPLICADA", f"Exame já presente na fila (item #{existente.id})."
            else:
                status_item, obs = "VALIDA", None

            if status_item in ("VALIDA", "JA_REALIZADA"):
                vistos_solicitacao.setdefault(chave_sol, linha.numero_linha)
                if chave_pront:
                    vistos_prontuario.setdefault(chave_pront, linha.numero_linha)

            resultado.append(ItemHigienizado(**item, status_higienizacao=status_item, observacoes=obs))

    return resultado


# ---------------------------------------------------------------------------
# Orquestração com I/O (AGHU + SQLite + auditoria)
# ---------------------------------------------------------------------------


async def _consultar_aghu(
    provider: ExameProviderInterface, linhas: List[LinhaForms]
) -> Dict[str, List[Dict[str, Any]]]:
    """Consulta no AGHU (somente leitura) cada número de solicitação distinto da planilha."""
    codigos = sorted({c for c in (somente_digitos(l.codigo_solicitacao_bruto) for l in linhas) if c})
    resultado: Dict[str, List[Dict[str, Any]]] = {}
    try:
        for codigo in codigos:
            resultado[codigo] = await provider.buscar_por_solicitacao(codigo)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Falha ao consultar a base do AGHU durante a higienização. Tente novamente.",
        ) from exc
    return resultado


async def _carregar_fila_existente(db: AsyncSession) -> List[RegistroFilaExistente]:
    """Carrega os itens válidos e não cancelados da fila para detectar duplicidades."""
    linhas = await db.execute(
        select(
            AcompanhamentoFila.id,
            AcompanhamentoFila.codigo_solicitacao,
            AcompanhamentoFila.codigo_exame,
            AcompanhamentoFila.prontuario,
            AcompanhamentoFila.status_operacional,
        ).where(
            AcompanhamentoFila.deleted_at.is_(None),
            AcompanhamentoFila.status_higienizacao == "VALIDA",
            AcompanhamentoFila.status_operacional != "CANCELADO",
        )
    )
    return [RegistroFilaExistente(*linha) for linha in linhas.all()]


def _truncar(valor: Optional[str], tamanho: int) -> Optional[str]:
    """Limita o texto ao tamanho da coluna (``None`` permanece ``None``)."""
    return valor[:tamanho] if valor else None


def contar_por_status(status_itens: Iterable[str]) -> Dict[str, int]:
    """Conta itens por status de higienização (todos os status presentes, inclusive zerados)."""
    contagem = Counter(status_itens)
    return {s: contagem.get(s, 0) for s in STATUS_HIGIENIZACAO_VALIDOS}


async def importar_planilha_forms(
    db: AsyncSession,
    provider: ExameProviderInterface,
    leitura: ResultadoLeituraPlanilha,
    nome_arquivo: str,
    usuario: str,
    ip_origem: Optional[str],
) -> Dict[str, Any]:
    """
    Executa a higienização ``Forms × AGHU``, persiste a importação e seus itens
    e registra a auditoria ``NEGOCIO_CLINICO`` em uma única transação.

    Returns:
        Dicionário com ``importacao`` (ORM), ``itens`` (lista de pares ORM/linha),
        ``contadores`` e o diagnóstico de colunas da planilha.
    """
    aghu = await _consultar_aghu(provider, leitura.linhas)
    itens = classificar_linhas(leitura.linhas, aghu, await _carregar_fila_existente(db))
    contadores = contar_por_status(i.status_higienizacao for i in itens)

    importacao = ImportacaoForms(
        nome_arquivo=nome_arquivo[:255],
        usuario_importador=usuario[:120],
        total_linhas=len(leitura.linhas),
        total_validas=contadores["VALIDA"],
        total_duplicadas=contadores["DUPLICADA"],
        total_erros=contadores["DIVERGENCIA_EXAME"] + contadores["NAO_ENCONTRADA"] + contadores["JA_REALIZADA"],
    )
    db.add(importacao)
    await db.flush()

    registros: List[Tuple[AcompanhamentoFila, int]] = []
    for item in itens:
        linha = item.linha
        registro = AcompanhamentoFila(
            importacao_id=importacao.id,
            codigo_solicitacao=item.codigo_solicitacao,
            codigo_exame=item.codigo_exame,
            prontuario=item.prontuario,
            nome_paciente=item.nome_paciente[:255],
            telefone_contato=_truncar(item.telefone_contato, 64),
            municipio=_truncar(item.municipio, 120),
            regiao_geografica=classificar_regiao(item.municipio),
            utiliza_tfd=linha.utiliza_tfd,
            data_retorno_medico=linha.data_retorno,
            exame_informado_forms=_truncar(linha.exame_informado, 255),
            unidade_solicitante=item.unidade_solicitante,
            especialidade_solicitante=item.especialidade_solicitante,
            idade_informada=linha.idade,
            status_higienizacao=item.status_higienizacao,
            status_operacional="NA_FILA",
            observacoes=item.observacoes,
        )
        db.add(registro)
        registros.append((registro, linha.numero_linha))
    await db.flush()

    await registrar_auditoria(
        db=db,
        usuario=usuario,
        categoria=CATEGORIA_AUDITORIA,
        acao="IMPORTAR_PLANILHA_FORMS",
        recurso=f"importacoes_forms:{importacao.id}",
        dados_anteriores=None,
        dados_novos={
            "nome_arquivo": importacao.nome_arquivo,
            "total_linhas": importacao.total_linhas,
            "contadores": contadores,
            "colunas_reconhecidas": leitura.colunas_reconhecidas,
        },
        ip_origem=ip_origem,
    )

    return {
        "importacao": importacao,
        "itens": registros,
        "contadores": contadores,
        "colunas_reconhecidas": leitura.colunas_reconhecidas,
        "colunas_ignoradas": leitura.colunas_ignoradas,
    }


async def listar_importacoes(db: AsyncSession, limite: int = 50, deslocamento: int = 0) -> List[ImportacaoForms]:
    """Lista o histórico de importações (mais recentes primeiro), sem as excluídas."""
    stmt = (
        select(ImportacaoForms)
        .where(ImportacaoForms.deleted_at.is_(None))
        .order_by(ImportacaoForms.importado_em.desc(), ImportacaoForms.id.desc())
        .limit(limite)
        .offset(deslocamento)
    )
    return list((await db.scalars(stmt)).all())


async def obter_importacao(db: AsyncSession, importacao_id: int) -> Dict[str, Any]:
    """Obtém uma importação com seus itens higienizados e contadores por status."""
    importacao = await db.get(ImportacaoForms, importacao_id)
    if importacao is None or importacao.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Importação não encontrada.")

    itens = list(
        (
            await db.scalars(
                select(AcompanhamentoFila)
                .where(AcompanhamentoFila.importacao_id == importacao.id, AcompanhamentoFila.deleted_at.is_(None))
                .order_by(AcompanhamentoFila.id)
            )
        ).all()
    )
    return {
        "importacao": importacao,
        "itens": [(item, None) for item in itens],
        "contadores": contar_por_status(i.status_higienizacao for i in itens),
    }
