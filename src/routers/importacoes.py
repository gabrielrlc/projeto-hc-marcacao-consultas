"""
Roteador de Importação do Google Forms (``/api/importacoes``) — TASK-007 / RF003
================================================================================
- ``POST /api/importacoes/forms``: upload CSV/XLSX da planilha do Forms,
  higienização ``Forms × AGHU`` e relatório com contadores e itens.
- ``GET /api/importacoes``: histórico de importações.
- ``GET /api/importacoes/{id}``: relatório de uma importação (itens e exceções).

Restrito aos perfis operacionais (``MARCADOR``, ``GESTOR_CENTRAL``,
``ADMINISTRADOR``). O arquivo é lido apenas em memória e não é armazenado.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from pydantic.alias_generators import to_camel
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import auth_handler
from ..auth.rbac import PERFIS_OPERACAO, obter_ip_origem, obter_usuario_logado, require_perfis
from ..config import settings
from ..controllers import importacao_controller
from ..dependencies import get_exame_provider
from ..helpers.planilha_forms_helper import TAMANHO_MAXIMO_BYTES, PlanilhaInvalidaError, ler_planilha_forms
from ..providers.interfaces.exame_provider_interface import ExameProviderInterface
from ..resources.database import get_app_db_session
from ..schemas.importacoes import ImportacaoResumoOut, ItemImportacaoOut, RelatorioImportacaoOut

# Fonte AGHU configurável via EXAME_PROVIDER_TYPE ("CSV" em dev, "POSTGRES" em produção)
STRATEGY = settings.EXAME_PROVIDER_TYPE

router = APIRouter(
    prefix="/api/importacoes",
    tags=["Importação Google Forms"],
    dependencies=[Depends(auth_handler.decode_token)],
)

_operacao = require_perfis(*PERFIS_OPERACAO)


def _montar_relatorio(resultado: Dict[str, Any]) -> RelatorioImportacaoOut:
    """Converte o resultado do controller no relatório de saída da API."""
    itens: List[ItemImportacaoOut] = []
    for registro, linha in resultado["itens"]:
        item = ItemImportacaoOut.model_validate(registro)
        item.linha_planilha = linha
        itens.append(item)
    return RelatorioImportacaoOut(
        importacao=ImportacaoResumoOut.model_validate(resultado["importacao"]),
        contadores=resultado["contadores"],
        colunas_reconhecidas={
            to_camel(campo): coluna for campo, coluna in resultado.get("colunas_reconhecidas", {}).items()
        },
        colunas_ignoradas=resultado.get("colunas_ignoradas", []),
        itens=itens,
    )


@router.post("/forms", response_model=RelatorioImportacaoOut, status_code=status.HTTP_201_CREATED)
async def importar_planilha_forms(
    request: Request,
    arquivo: UploadFile = File(..., description="Planilha exportada do Google Forms (.csv ou .xlsx)."),
    usuario: Dict[str, Any] = Depends(_operacao),
    provider: ExameProviderInterface = Depends(get_exame_provider(STRATEGY)),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Importa e higieniza a planilha do Forms contra o AGHU, retornando o relatório."""
    conteudo = await arquivo.read(TAMANHO_MAXIMO_BYTES + 1)
    nome_arquivo = arquivo.filename or "planilha_forms"
    try:
        leitura = ler_planilha_forms(conteudo, nome_arquivo)
    except PlanilhaInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    resultado = await importacao_controller.importar_planilha_forms(
        db, provider, leitura, nome_arquivo, obter_usuario_logado(usuario), obter_ip_origem(request)
    )
    return _montar_relatorio(resultado)


@router.get("", response_model=List[ImportacaoResumoOut], dependencies=[Depends(_operacao)])
async def listar_importacoes(
    limite: int = Query(50, ge=1, le=200),
    deslocamento: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Lista o histórico de importações, das mais recentes para as mais antigas."""
    return await importacao_controller.listar_importacoes(db, limite=limite, deslocamento=deslocamento)


@router.get("/{importacao_id}", response_model=RelatorioImportacaoOut, dependencies=[Depends(_operacao)])
async def obter_importacao(importacao_id: int, db: AsyncSession = Depends(get_app_db_session)):
    """Retorna o relatório de uma importação com os itens válidos e as exceções."""
    return _montar_relatorio(await importacao_controller.obter_importacao(db, importacao_id))
