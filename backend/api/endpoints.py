from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from application.dtos import LoginRequest, TokenResponse
from infrastructure.auth_provider import AuthProvider
from api.dependencies import get_user_repository
from api.guards import require_role, require_any_role
from domain.enums import UserRole
from domain.entities import User

router = APIRouter(tags=["AccessFlow API"])

# ============================================================
# Auth Endpoints (Issue 89)
# ============================================================

@router.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login(request: LoginRequest, user_repo = Depends(get_user_repository)):
    """Autentica a un usuario validando su email y contraseña."""
    user = user_repo.get_by_email(request.email)
    
    if not user or not AuthProvider.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = AuthProvider.create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "user_id": str(user.id)
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value
    )


# ============================================================
# Access Request Endpoints (Issue 90)
# ============================================================

# Dummy DTO para que no falle el endpoint de crear
class CreateRequestDTO(BaseModel):
    target_system: str
    justification: str


@router.post("/requests", status_code=status.HTTP_201_CREATED, tags=["Access Requests"])
def create_access_request(
    payload: CreateRequestDTO,
    # Cualquier rol válido puede crear solicitudes (Employee o superior)
    current_user: User = Depends(require_any_role([
        UserRole.EMPLOYEE, 
        UserRole.MANAGER, 
        UserRole.SECURITY_REVIEWER, 
        UserRole.IT_ADMIN
    ]))
):
    """Crea una nueva solicitud de acceso."""
    return {"message": "Solicitud creada exitosamente", "requester": current_user.email}


@router.post("/requests/{request_id}/approve", tags=["Access Requests"])
def approve_request(
    request_id: str,
    # Solo los Managers pueden aprobar el primer paso
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Aprueba una solicitud en la fase de Manager."""
    return {"message": f"Solicitud {request_id} aprobada por el manager {current_user.email}"}


@router.post("/requests/{request_id}/security-review", tags=["Access Requests"])
def security_review_request(
    request_id: str,
    # Solo el equipo de Seguridad puede hacer estas revisiones
    current_user: User = Depends(require_role(UserRole.SECURITY_REVIEWER))
):
    """Aprueba o revisa una solicitud en la fase de Seguridad."""
    return {"message": f"Solicitud {request_id} aprobada por seguridad ({current_user.email})"}


@router.post("/requests/{request_id}/provision", tags=["Access Requests"])
def provision_request(
    request_id: str,
    # Solo IT Admin puede dar el acceso final en el sistema real
    current_user: User = Depends(require_role(UserRole.IT_ADMIN))
):
    """Ejecuta el aprovisionamiento de una solicitud lista."""
    return {"message": f"Acceso provisionado para la solicitud {request_id} por {current_user.email}"}