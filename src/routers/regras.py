"""
Roteador de Regras Configuráveis (``/api/regras``) — TASK-006 / RF009
=====================================================================
CRUD (com soft delete) de Pesos de Prioridade, Regras por Exame e Matriz de
Incompatibilidades.

- **Leitura (GET):** qualquer perfil válido da aplicação (o motor de prioridade
  e a tela da fila também consomem estas regras).
- **Escrita (POST/PUT/DELETE):** restrita a ``GESTOR_CENTRAL`` e ``ADMINISTRADOR``.
- **Respostas:** camelCase; ``DELETE`` retorna ``204`` (exclusão lógica).
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import auth_handler
from ..auth.rbac import PERFIS_GESTAO, PERFIS_LEITURA, obter_ip_origem, obter_usuario_logado, require_perfis
from ..controllers import regras_controller
from ..resources.database import get_app_db_session
from ..schemas.regras import (
    IncompatibilidadeExameIn,
    IncompatibilidadeExameOut,
    RegraExameCreate,
    RegraExameOut,
    RegraExameUpdate,
    RegraPrioridadeCreate,
    RegraPrioridadeOut,
    RegraPrioridadeUpdate,
)

router = APIRouter(
    prefix="/api/regras",
    tags=["Regras Configuráveis"],
    dependencies=[Depends(auth_handler.decode_token)],
)

_leitura = require_perfis(*PERFIS_LEITURA)
_gestao = require_perfis(*PERFIS_GESTAO)

_FILTRO_ATIVO = Query(None, description="Filtra por situação ativa/inativa. Omitido: retorna ambos.")


# ---------------------------------------------------------------------------
# Pesos de Prioridade
# ---------------------------------------------------------------------------


@router.get("/prioridades", response_model=List[RegraPrioridadeOut], dependencies=[Depends(_leitura)])
async def listar_prioridades(
    ativo: Optional[bool] = _FILTRO_ATIVO,
    db: AsyncSession = Depends(get_app_db_session),
):
    """Lista os grupos e pesos de prioridade clínica (excluídos não aparecem)."""
    return await regras_controller.listar_prioridades(db, ativo=ativo)


@router.get("/prioridades/{regra_id}", response_model=RegraPrioridadeOut, dependencies=[Depends(_leitura)])
async def obter_prioridade(regra_id: int, db: AsyncSession = Depends(get_app_db_session)):
    """Obtém uma regra de prioridade pelo identificador."""
    return await regras_controller.obter_prioridade(db, regra_id)


@router.post("/prioridades", response_model=RegraPrioridadeOut, status_code=status.HTTP_201_CREATED)
async def criar_prioridade(
    dados: RegraPrioridadeCreate,
    request: Request,
    usuario: Dict[str, Any] = Depends(_gestao),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Cadastra uma regra de prioridade (reativa o código se ele estiver excluído)."""
    return await regras_controller.criar_prioridade(
        db, dados, obter_usuario_logado(usuario), obter_ip_origem(request)
    )


@router.put("/prioridades/{regra_id}", response_model=RegraPrioridadeOut)
async def atualizar_prioridade(
    regra_id: int,
    dados: RegraPrioridadeUpdate,
    request: Request,
    usuario: Dict[str, Any] = Depends(_gestao),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Atualiza nome, critério, valor de correspondência, peso, situação e descrição."""
    return await regras_controller.atualizar_prioridade(
        db, regra_id, dados, obter_usuario_logado(usuario), obter_ip_origem(request)
    )


@router.delete("/prioridades/{regra_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_prioridade(
    regra_id: int,
    request: Request,
    usuario: Dict[str, Any] = Depends(_gestao),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Exclui logicamente uma regra de prioridade."""
    await regras_controller.excluir_prioridade(db, regra_id, obter_usuario_logado(usuario), obter_ip_origem(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Regras por Exame
# ---------------------------------------------------------------------------


@router.get("/exames", response_model=List[RegraExameOut], dependencies=[Depends(_leitura)])
async def listar_regras_exames(
    ativo: Optional[bool] = _FILTRO_ATIVO,
    busca: Optional[str] = Query(None, max_length=100, description="Trecho do código ou nome do exame."),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Lista as regras de preparo, retorno e alertas por exame."""
    return await regras_controller.listar_regras_exames(db, ativo=ativo, busca=busca)


@router.get("/exames/{regra_id}", response_model=RegraExameOut, dependencies=[Depends(_leitura)])
async def obter_regra_exame(regra_id: int, db: AsyncSession = Depends(get_app_db_session)):
    """Obtém uma regra de exame pelo identificador."""
    return await regras_controller.obter_regra_exame(db, regra_id)


@router.post("/exames", response_model=RegraExameOut, status_code=status.HTTP_201_CREATED)
async def criar_regra_exame(
    dados: RegraExameCreate,
    request: Request,
    usuario: Dict[str, Any] = Depends(_gestao),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Cadastra a regra de um exame pela sigla do AGHU (reativa se estiver excluída)."""
    return await regras_controller.criar_regra_exame(
        db, dados, obter_usuario_logado(usuario), obter_ip_origem(request)
    )


@router.put("/exames/{regra_id}", response_model=RegraExameOut)
async def atualizar_regra_exame(
    regra_id: int,
    dados: RegraExameUpdate,
    request: Request,
    usuario: Dict[str, Any] = Depends(_gestao),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Atualiza preparo, antecedência, janela de retorno, jejum e alertas do exame."""
    return await regras_controller.atualizar_regra_exame(
        db, regra_id, dados, obter_usuario_logado(usuario), obter_ip_origem(request)
    )


@router.delete("/exames/{regra_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_regra_exame(
    regra_id: int,
    request: Request,
    usuario: Dict[str, Any] = Depends(_gestao),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Exclui logicamente uma regra de exame (bloqueado se houver incompatibilidades como origem)."""
    await regras_controller.excluir_regra_exame(db, regra_id, obter_usuario_logado(usuario), obter_ip_origem(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Matriz de Incompatibilidades
# ---------------------------------------------------------------------------


@router.get("/incompatibilidades", response_model=List[IncompatibilidadeExameOut], dependencies=[Depends(_leitura)])
async def listar_incompatibilidades(
    ativo: Optional[bool] = _FILTRO_ATIVO,
    codigo_exame: Optional[str] = Query(
        None, max_length=50, description="Sigla do exame em qualquer lado do par."
    ),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Lista os pares de exames incompatíveis."""
    return await regras_controller.listar_incompatibilidades(db, ativo=ativo, codigo_exame=codigo_exame)


@router.get(
    "/incompatibilidades/{incompatibilidade_id}",
    response_model=IncompatibilidadeExameOut,
    dependencies=[Depends(_leitura)],
)
async def obter_incompatibilidade(incompatibilidade_id: int, db: AsyncSession = Depends(get_app_db_session)):
    """Obtém um par de exames incompatíveis pelo identificador."""
    return await regras_controller.obter_incompatibilidade(db, incompatibilidade_id)


@router.post("/incompatibilidades", response_model=IncompatibilidadeExameOut, status_code=status.HTTP_201_CREATED)
async def criar_incompatibilidade(
    dados: IncompatibilidadeExameIn,
    request: Request,
    usuario: Dict[str, Any] = Depends(_gestao),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Cadastra um par de exames incompatíveis (Exame A × Exame B)."""
    return await regras_controller.criar_incompatibilidade(
        db, dados, obter_usuario_logado(usuario), obter_ip_origem(request)
    )


@router.put("/incompatibilidades/{incompatibilidade_id}", response_model=IncompatibilidadeExameOut)
async def atualizar_incompatibilidade(
    incompatibilidade_id: int,
    dados: IncompatibilidadeExameIn,
    request: Request,
    usuario: Dict[str, Any] = Depends(_gestao),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Atualiza um par de exames incompatíveis."""
    return await regras_controller.atualizar_incompatibilidade(
        db, incompatibilidade_id, dados, obter_usuario_logado(usuario), obter_ip_origem(request)
    )


@router.delete("/incompatibilidades/{incompatibilidade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_incompatibilidade(
    incompatibilidade_id: int,
    request: Request,
    usuario: Dict[str, Any] = Depends(_gestao),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Exclui logicamente um par de exames incompatíveis."""
    await regras_controller.excluir_incompatibilidade(
        db, incompatibilidade_id, obter_usuario_logado(usuario), obter_ip_origem(request)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
