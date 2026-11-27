"""
Controller de Regras Configuráveis (TASK-006 / RF009 / UC006)
=============================================================
Regras de negócio do CRUD de Pesos de Prioridade, Regras por Exame e Matriz de
Incompatibilidades no banco local (``data/app.db``):

- **Soft delete obrigatório:** exclusões preenchem ``deleted_at`` e desativam o
  registro (``ativo=False``); nenhum ``DELETE`` físico é emitido.
- **Unicidade:** ``codigo`` (prioridade) e ``codigo_exame`` (exame) são únicos
  inclusive entre registros excluídos. Um ``POST`` com o código de um registro
  excluído **reativa** esse registro com os novos dados (auditado como
  ``REATIVAR_*``); com código de registro ativo retorna ``409``.
- **Integridade da matriz:** o exame de origem de uma incompatibilidade deve
  ter regra de exame cadastrada (não excluída); o par A×B é único em qualquer
  ordem; uma regra de exame com incompatibilidades ativas não pode ser excluída.
- **Auditoria:** toda mutação chama ``registrar_auditoria()`` na categoria
  ``CONFIGURACAO`` com estado anterior e novo. A mutação é apenas ``flush``-ada
  e o commit ocorre dentro do helper de auditoria, tornando as duas gravações
  atômicas.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import inspect, or_, and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..helpers.audit_helper import registrar_auditoria
from ..models import IncompatibilidadeExame, RegraExame, RegraPrioridade
from ..resources.database import Base
from ..schemas.regras import (
    IncompatibilidadeExameIn,
    RegraExameCreate,
    RegraExameUpdate,
    RegraPrioridadeCreate,
    RegraPrioridadeUpdate,
)

CATEGORIA_AUDITORIA = "CONFIGURACAO"

ModelT = TypeVar("ModelT", bound=Base)


# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    """Retorna o timestamp atual em UTC."""
    return datetime.now(timezone.utc)


def serializar_registro(registro: Any) -> Dict[str, Any]:
    """Converte um registro ORM em dicionário ``coluna -> valor`` para auditoria."""
    return {attr.key: getattr(registro, attr.key) for attr in inspect(registro).mapper.column_attrs}


async def _obter_ativo_ou_404(
    db: AsyncSession, modelo: Type[ModelT], registro_id: int, descricao: str
) -> ModelT:
    """Busca um registro não excluído pelo ``id`` ou lança ``404``."""
    registro = await db.get(modelo, registro_id)
    if registro is None or registro.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{descricao} não encontrada.",
        )
    return registro


async def _persistir_com_auditoria(
    db: AsyncSession,
    registro: Any,
    *,
    usuario: str,
    acao: str,
    recurso_tabela: str,
    dados_anteriores: Optional[Dict[str, Any]],
    ip_origem: Optional[str],
    mensagem_conflito: str,
) -> Any:
    """
    Faz ``flush`` da mutação e registra a auditoria (que efetiva o commit).
    Violações de unicidade concorrentes são convertidas em ``409``.
    """
    db.add(registro)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=mensagem_conflito) from exc

    await registrar_auditoria(
        db=db,
        usuario=usuario,
        categoria=CATEGORIA_AUDITORIA,
        acao=acao,
        recurso=f"{recurso_tabela}:{registro.id}",
        dados_anteriores=dados_anteriores,
        dados_novos=serializar_registro(registro),
        ip_origem=ip_origem,
    )
    await db.refresh(registro)
    return registro


async def _excluir_logicamente(
    db: AsyncSession,
    registro: Any,
    *,
    usuario: str,
    acao: str,
    recurso_tabela: str,
    ip_origem: Optional[str],
) -> None:
    """Aplica soft delete (``deleted_at`` + ``ativo=False``) com auditoria."""
    anteriores = serializar_registro(registro)
    registro.deleted_at = _utc_now()
    registro.ativo = False
    await db.flush()
    await registrar_auditoria(
        db=db,
        usuario=usuario,
        categoria=CATEGORIA_AUDITORIA,
        acao=acao,
        recurso=f"{recurso_tabela}:{registro.id}",
        dados_anteriores=anteriores,
        dados_novos=serializar_registro(registro),
        ip_origem=ip_origem,
    )


def _aplicar_campos(registro: Any, dados: Dict[str, Any]) -> bool:
    """Copia os campos informados para o registro; retorna se houve alteração."""
    alterou = False
    for campo, valor in dados.items():
        if getattr(registro, campo) != valor:
            setattr(registro, campo, valor)
            alterou = True
    return alterou


# ---------------------------------------------------------------------------
# Pesos de Prioridade (regras_prioridade)
# ---------------------------------------------------------------------------

_DESC_PRIORIDADE = "Regra de prioridade"
_TABELA_PRIORIDADE = "regras_prioridade"


async def listar_prioridades(db: AsyncSession, ativo: Optional[bool] = None) -> List[RegraPrioridade]:
    """Lista regras de prioridade não excluídas, ordenadas por peso decrescente."""
    stmt = select(RegraPrioridade).where(RegraPrioridade.deleted_at.is_(None))
    if ativo is not None:
        stmt = stmt.where(RegraPrioridade.ativo.is_(ativo))
    stmt = stmt.order_by(RegraPrioridade.peso.desc(), RegraPrioridade.codigo)
    return list((await db.scalars(stmt)).all())


async def obter_prioridade(db: AsyncSession, regra_id: int) -> RegraPrioridade:
    """Obtém uma regra de prioridade não excluída pelo ``id``."""
    return await _obter_ativo_ou_404(db, RegraPrioridade, regra_id, _DESC_PRIORIDADE)


async def criar_prioridade(
    db: AsyncSession, dados: RegraPrioridadeCreate, usuario: str, ip_origem: Optional[str]
) -> RegraPrioridade:
    """Cria (ou reativa, se o código pertencer a um registro excluído) uma regra de prioridade."""
    existente = await db.scalar(select(RegraPrioridade).where(RegraPrioridade.codigo == dados.codigo))
    if existente is not None and existente.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe uma regra de prioridade com o código '{dados.codigo}'.",
        )

    campos = dados.model_dump(by_alias=False)
    if existente is not None:
        anteriores = serializar_registro(existente)
        _aplicar_campos(existente, campos)
        existente.deleted_at = None
        registro, acao = existente, "REATIVAR_REGRA_PRIORIDADE"
    else:
        anteriores = None
        registro, acao = RegraPrioridade(**campos), "CRIAR_REGRA_PRIORIDADE"

    return await _persistir_com_auditoria(
        db, registro, usuario=usuario, acao=acao, recurso_tabela=_TABELA_PRIORIDADE,
        dados_anteriores=anteriores, ip_origem=ip_origem,
        mensagem_conflito=f"Já existe uma regra de prioridade com o código '{dados.codigo}'.",
    )


async def atualizar_prioridade(
    db: AsyncSession, regra_id: int, dados: RegraPrioridadeUpdate, usuario: str, ip_origem: Optional[str]
) -> RegraPrioridade:
    """Atualiza os campos editáveis de uma regra de prioridade (código imutável)."""
    registro = await obter_prioridade(db, regra_id)
    anteriores = serializar_registro(registro)
    if not _aplicar_campos(registro, dados.model_dump(by_alias=False)):
        return registro
    return await _persistir_com_auditoria(
        db, registro, usuario=usuario, acao="ALTERAR_REGRA_PRIORIDADE",
        recurso_tabela=_TABELA_PRIORIDADE, dados_anteriores=anteriores, ip_origem=ip_origem,
        mensagem_conflito="Conflito ao atualizar a regra de prioridade.",
    )


async def excluir_prioridade(db: AsyncSession, regra_id: int, usuario: str, ip_origem: Optional[str]) -> None:
    """Exclui logicamente uma regra de prioridade."""
    registro = await obter_prioridade(db, regra_id)
    await _excluir_logicamente(
        db, registro, usuario=usuario, acao="EXCLUIR_REGRA_PRIORIDADE",
        recurso_tabela=_TABELA_PRIORIDADE, ip_origem=ip_origem,
    )


# ---------------------------------------------------------------------------
# Regras por Exame (regras_exames)
# ---------------------------------------------------------------------------

_DESC_EXAME = "Regra de exame"
_TABELA_EXAME = "regras_exames"


async def listar_regras_exames(
    db: AsyncSession, ativo: Optional[bool] = None, busca: Optional[str] = None
) -> List[RegraExame]:
    """Lista regras de exame não excluídas, com filtro opcional por código/nome."""
    stmt = select(RegraExame).where(RegraExame.deleted_at.is_(None))
    if ativo is not None:
        stmt = stmt.where(RegraExame.ativo.is_(ativo))
    if busca:
        termo = f"%{busca.strip()}%"
        stmt = stmt.where(or_(RegraExame.codigo_exame.ilike(termo), RegraExame.nome_exame.ilike(termo)))
    stmt = stmt.order_by(RegraExame.codigo_exame)
    return list((await db.scalars(stmt)).all())


async def obter_regra_exame(db: AsyncSession, regra_id: int) -> RegraExame:
    """Obtém uma regra de exame não excluída pelo ``id``."""
    return await _obter_ativo_ou_404(db, RegraExame, regra_id, _DESC_EXAME)


async def criar_regra_exame(
    db: AsyncSession, dados: RegraExameCreate, usuario: str, ip_origem: Optional[str]
) -> RegraExame:
    """Cria (ou reativa, se o código pertencer a um registro excluído) uma regra de exame."""
    existente = await db.scalar(select(RegraExame).where(RegraExame.codigo_exame == dados.codigo_exame))
    if existente is not None and existente.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe uma regra cadastrada para o exame '{dados.codigo_exame}'.",
        )

    campos = dados.model_dump(by_alias=False)
    if existente is not None:
        anteriores = serializar_registro(existente)
        _aplicar_campos(existente, campos)
        existente.deleted_at = None
        registro, acao = existente, "REATIVAR_REGRA_EXAME"
    else:
        anteriores = None
        registro, acao = RegraExame(**campos), "CRIAR_REGRA_EXAME"

    return await _persistir_com_auditoria(
        db, registro, usuario=usuario, acao=acao, recurso_tabela=_TABELA_EXAME,
        dados_anteriores=anteriores, ip_origem=ip_origem,
        mensagem_conflito=f"Já existe uma regra cadastrada para o exame '{dados.codigo_exame}'.",
    )


async def atualizar_regra_exame(
    db: AsyncSession, regra_id: int, dados: RegraExameUpdate, usuario: str, ip_origem: Optional[str]
) -> RegraExame:
    """Atualiza os campos editáveis de uma regra de exame (sigla do exame imutável)."""
    registro = await obter_regra_exame(db, regra_id)
    anteriores = serializar_registro(registro)
    if not _aplicar_campos(registro, dados.model_dump(by_alias=False)):
        return registro
    return await _persistir_com_auditoria(
        db, registro, usuario=usuario, acao="ALTERAR_REGRA_EXAME",
        recurso_tabela=_TABELA_EXAME, dados_anteriores=anteriores, ip_origem=ip_origem,
        mensagem_conflito="Conflito ao atualizar a regra de exame.",
    )


async def excluir_regra_exame(db: AsyncSession, regra_id: int, usuario: str, ip_origem: Optional[str]) -> None:
    """Exclui logicamente uma regra de exame sem incompatibilidades ativas como origem."""
    registro = await obter_regra_exame(db, regra_id)
    dependentes = await db.scalar(
        select(IncompatibilidadeExame.id).where(
            IncompatibilidadeExame.codigo_exame_origem == registro.codigo_exame,
            IncompatibilidadeExame.deleted_at.is_(None),
        ).limit(1)
    )
    if dependentes is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"O exame '{registro.codigo_exame}' possui incompatibilidades cadastradas como origem. "
                "Exclua-as antes de excluir a regra do exame."
            ),
        )
    await _excluir_logicamente(
        db, registro, usuario=usuario, acao="EXCLUIR_REGRA_EXAME",
        recurso_tabela=_TABELA_EXAME, ip_origem=ip_origem,
    )


# ---------------------------------------------------------------------------
# Matriz de Incompatibilidades (incompatibilidades_exames)
# ---------------------------------------------------------------------------

_DESC_INCOMPATIBILIDADE = "Incompatibilidade de exames"
_TABELA_INCOMPATIBILIDADE = "incompatibilidades_exames"


async def listar_incompatibilidades(
    db: AsyncSession, ativo: Optional[bool] = None, codigo_exame: Optional[str] = None
) -> List[IncompatibilidadeExame]:
    """Lista incompatibilidades não excluídas, com filtro por exame (em qualquer lado do par)."""
    stmt = select(IncompatibilidadeExame).where(IncompatibilidadeExame.deleted_at.is_(None))
    if ativo is not None:
        stmt = stmt.where(IncompatibilidadeExame.ativo.is_(ativo))
    if codigo_exame:
        codigo = codigo_exame.strip().upper()
        stmt = stmt.where(
            or_(
                IncompatibilidadeExame.codigo_exame_origem == codigo,
                IncompatibilidadeExame.codigo_exame_conflitante == codigo,
            )
        )
    stmt = stmt.order_by(IncompatibilidadeExame.codigo_exame_origem, IncompatibilidadeExame.codigo_exame_conflitante)
    return list((await db.scalars(stmt)).all())


async def obter_incompatibilidade(db: AsyncSession, incompatibilidade_id: int) -> IncompatibilidadeExame:
    """Obtém uma incompatibilidade não excluída pelo ``id``."""
    return await _obter_ativo_ou_404(db, IncompatibilidadeExame, incompatibilidade_id, _DESC_INCOMPATIBILIDADE)


async def _validar_incompatibilidade(
    db: AsyncSession, dados: IncompatibilidadeExameIn, ignorar_id: Optional[int] = None
) -> None:
    """Valida a existência da regra do exame de origem e a unicidade do par A×B."""
    origem = await db.scalar(
        select(RegraExame.id).where(
            RegraExame.codigo_exame == dados.codigo_exame_origem,
            RegraExame.deleted_at.is_(None),
        )
    )
    if origem is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"O exame de origem '{dados.codigo_exame_origem}' não possui regra de exame cadastrada. "
                "Cadastre-o em Regras por Exame antes de criar a incompatibilidade."
            ),
        )

    a, b = dados.codigo_exame_origem, dados.codigo_exame_conflitante
    stmt = select(IncompatibilidadeExame.id).where(
        IncompatibilidadeExame.deleted_at.is_(None),
        or_(
            and_(IncompatibilidadeExame.codigo_exame_origem == a, IncompatibilidadeExame.codigo_exame_conflitante == b),
            and_(IncompatibilidadeExame.codigo_exame_origem == b, IncompatibilidadeExame.codigo_exame_conflitante == a),
        ),
    )
    if ignorar_id is not None:
        stmt = stmt.where(IncompatibilidadeExame.id != ignorar_id)
    if await db.scalar(stmt.limit(1)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe uma incompatibilidade cadastrada entre '{a}' e '{b}'.",
        )


async def criar_incompatibilidade(
    db: AsyncSession, dados: IncompatibilidadeExameIn, usuario: str, ip_origem: Optional[str]
) -> IncompatibilidadeExame:
    """Cadastra um novo par de exames incompatíveis."""
    await _validar_incompatibilidade(db, dados)
    registro = IncompatibilidadeExame(**dados.model_dump(by_alias=False))
    return await _persistir_com_auditoria(
        db, registro, usuario=usuario, acao="CRIAR_INCOMPATIBILIDADE_EXAME",
        recurso_tabela=_TABELA_INCOMPATIBILIDADE, dados_anteriores=None, ip_origem=ip_origem,
        mensagem_conflito="Conflito ao cadastrar a incompatibilidade de exames.",
    )


async def atualizar_incompatibilidade(
    db: AsyncSession, incompatibilidade_id: int, dados: IncompatibilidadeExameIn, usuario: str, ip_origem: Optional[str]
) -> IncompatibilidadeExame:
    """Atualiza um par de exames incompatíveis, revalidando origem e unicidade."""
    registro = await obter_incompatibilidade(db, incompatibilidade_id)
    await _validar_incompatibilidade(db, dados, ignorar_id=registro.id)
    anteriores = serializar_registro(registro)
    if not _aplicar_campos(registro, dados.model_dump(by_alias=False)):
        return registro
    return await _persistir_com_auditoria(
        db, registro, usuario=usuario, acao="ALTERAR_INCOMPATIBILIDADE_EXAME",
        recurso_tabela=_TABELA_INCOMPATIBILIDADE, dados_anteriores=anteriores, ip_origem=ip_origem,
        mensagem_conflito="Conflito ao atualizar a incompatibilidade de exames.",
    )


async def excluir_incompatibilidade(
    db: AsyncSession, incompatibilidade_id: int, usuario: str, ip_origem: Optional[str]
) -> None:
    """Exclui logicamente um par de exames incompatíveis."""
    registro = await obter_incompatibilidade(db, incompatibilidade_id)
    await _excluir_logicamente(
        db, registro, usuario=usuario, acao="EXCLUIR_INCOMPATIBILIDADE_EXAME",
        recurso_tabela=_TABELA_INCOMPATIBILIDADE, ip_origem=ip_origem,
    )
