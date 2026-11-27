"""
Controle de Acesso Baseado em Perfis (RBAC Local)
=================================================
Converte os grupos do Active Directory presentes no JWT em perfis da aplicação
(``ADMINISTRADOR``, ``GESTOR_CENTRAL``, ``MARCADOR``, ``CONSULTA``) segundo o
mapeamento configurado em ``src/config.py`` (variáveis ``RBAC_GRUPOS_*``) e
fornece dependências FastAPI para restringir rotas por perfil.

Uso em um roteador::

    from ..auth.rbac import require_perfis

    @router.post("", dependencies=[Depends(require_perfis("GESTOR_CENTRAL"))])
    async def criar(...): ...

    # ou, para obter o usuário autenticado com seus perfis resolvidos:
    async def criar(usuario: dict = Depends(require_perfis("GESTOR_CENTRAL"))): ...

O perfil ``ADMINISTRADOR`` possui acesso total e é aceito em qualquer rota
protegida por ``require_perfis``.
"""

from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional

from fastapi import Depends, HTTPException, Request, status

from ..config import settings
from .auth import auth_handler

PERFIL_ADMINISTRADOR = "ADMINISTRADOR"
PERFIL_GESTOR_CENTRAL = "GESTOR_CENTRAL"
PERFIL_MARCADOR = "MARCADOR"
PERFIL_CONSULTA = "CONSULTA"

PERFIS_VALIDOS: tuple[str, ...] = (
    PERFIL_ADMINISTRADOR,
    PERFIL_GESTOR_CENTRAL,
    PERFIL_MARCADOR,
    PERFIL_CONSULTA,
)

# Conjuntos usuais de perfis para reutilização nos roteadores
PERFIS_GESTAO: tuple[str, ...] = (PERFIL_ADMINISTRADOR, PERFIL_GESTOR_CENTRAL)
PERFIS_OPERACAO: tuple[str, ...] = (
    PERFIL_ADMINISTRADOR,
    PERFIL_GESTOR_CENTRAL,
    PERFIL_MARCADOR,
)
PERFIS_LEITURA: tuple[str, ...] = PERFIS_VALIDOS


def obter_mapa_grupos_perfis() -> Dict[str, List[str]]:
    """
    Retorna o mapeamento atual ``perfil -> grupos do AD`` lido das
    configurações centralizadas (``settings.RBAC_GRUPOS_*``).
    """
    return {
        PERFIL_ADMINISTRADOR: list(settings.RBAC_GRUPOS_ADMINISTRADOR),
        PERFIL_GESTOR_CENTRAL: list(settings.RBAC_GRUPOS_GESTOR_CENTRAL),
        PERFIL_MARCADOR: list(settings.RBAC_GRUPOS_MARCADOR),
        PERFIL_CONSULTA: list(settings.RBAC_GRUPOS_CONSULTA),
    }


def resolver_perfis(grupos: Optional[Iterable[Any]]) -> List[str]:
    """
    Converte a lista de grupos do AD de um usuário nos perfis da aplicação.

    A comparação ignora maiúsculas/minúsculas e espaços nas extremidades. O
    resultado segue a ordem de ``PERFIS_VALIDOS`` e não contém repetições.
    """
    grupos_usuario = {
        str(grupo).strip().upper() for grupo in (grupos or []) if str(grupo).strip()
    }
    if not grupos_usuario:
        return []

    perfis: List[str] = []
    for perfil, grupos_perfil in obter_mapa_grupos_perfis().items():
        grupos_normalizados = {g.strip().upper() for g in grupos_perfil if g.strip()}
        if grupos_usuario & grupos_normalizados:
            perfis.append(perfil)
    return perfis


def require_perfis(*perfis_permitidos: str) -> Callable[..., Awaitable[Dict[str, Any]]]:
    """
    Cria uma dependência FastAPI que exige que o usuário autenticado possua ao
    menos um dos perfis informados (ou ``ADMINISTRADOR``).

    Retorna, na injeção, o payload do JWT acrescido da chave ``perfis``.

    Raises:
        ValueError: se algum perfil informado não existir em ``PERFIS_VALIDOS``
            (erro de programação detectado na importação do roteador).
    """
    if not perfis_permitidos:
        raise ValueError("Informe ao menos um perfil em require_perfis().")
    desconhecidos = [p for p in perfis_permitidos if p not in PERFIS_VALIDOS]
    if desconhecidos:
        raise ValueError(f"Perfis desconhecidos em require_perfis(): {desconhecidos}")

    permitidos = set(perfis_permitidos) | {PERFIL_ADMINISTRADOR}

    async def _verificar_perfis(
        current_user: Dict[str, Any] = Depends(auth_handler.decode_token),
    ) -> Dict[str, Any]:
        """Valida os perfis do usuário autenticado contra os perfis permitidos."""
        perfis_usuario = resolver_perfis(current_user.get("groups"))
        if not permitidos.intersection(perfis_usuario):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: seu perfil não possui permissão para esta operação.",
            )
        return {**current_user, "perfis": perfis_usuario}

    return _verificar_perfis


def obter_usuario_logado(current_user: Dict[str, Any]) -> str:
    """Retorna o login do usuário autenticado a partir do payload do JWT."""
    return str(current_user.get("username") or current_user.get("sub") or "desconhecido")


def obter_ip_origem(request: Request) -> Optional[str]:
    """Retorna o IP de origem da requisição para registro em ``audit_logs``."""
    return request.client.host if request.client else None
