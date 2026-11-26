from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..auth.auth import auth_handler
from ..controllers import auditoria_controller
from ..dependencies import get_auditoria_provider
from ..providers.interfaces.auditoria_provider_interface import AuditoriaProviderInterface
from ..schemas.auditoria import AuditLogPage, CategoriaAuditoria

router = APIRouter(
    prefix="/api", tags=["Admin"], dependencies=[Depends(auth_handler.decode_token)]
)

class AdminData(BaseModel):
    message: str
    user_groups: List[str]

async def verify_admin_group(current_user: dict = Depends(auth_handler.decode_token)) -> dict:
    """Exige o grupo administrativo usado atualmente pelo framework."""
    ADMIN_GROUP = "GLO-SEC-HCPE-SETISD"
    if ADMIN_GROUP not in current_user.get("groups", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    return current_user


@router.get("/admin/audit-logs", response_model=AuditLogPage, dependencies=[Depends(verify_admin_group)])
async def listar_audit_logs(
    provider: Annotated[AuditoriaProviderInterface, Depends(get_auditoria_provider)],
    categoria: CategoriaAuditoria | None = None,
    usuario: Annotated[str | None, Query(min_length=1)] = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> AuditLogPage:
    """Consulta a trilha imutável; datas delimitam um período inclusivo em UTC."""
    return await auditoria_controller.listar_logs(
        provider, categoria, usuario, data_inicio, data_fim, page, page_size
    )

@router.get("/admin-only-data", response_model=AdminData)
async def get_admin_data(current_user: dict = Depends(verify_admin_group)):
    """
    Returns data only accessible by users with admin privileges.
    """
    return AdminData(
        message="This is highly confidential admin data!",
        user_groups=current_user.get("groups", [])
    )

class ADUserSearchResponse(BaseModel):
    exists: bool
    username: str
    displayName: str
    email: str
    department: str

@router.get("/admin/ad-user-search/{username}", response_model=ADUserSearchResponse)
async def search_ad_user(username: str, current_user: dict = Depends(verify_admin_group)):
    """
    Busca e valida um usuário no Active Directory (ou Mock) pelo login de rede.
    Restrito a administradores do sistema.
    """
    res = auth_handler.search_ad_user(username)
    return ADUserSearchResponse(**res)
