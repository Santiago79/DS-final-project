from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from application.dtos import (
    LoginRequest, TokenResponse, CreateAccessRequestDTO, 
    AccessRequestResponse, ActionReasonDTO, 
    NotificationResponse, AuditLogResponse
)
from infrastructure.auth_provider import AuthProvider
from api.dependencies import get_user_repository, get_current_user, get_access_request_use_cases
from api.guards import require_role, require_any_role
from domain.enums import UserRole
from domain.entities import User
from application.use_cases import AccessRequestUseCases

router = APIRouter(tags=["AccessFlow API"])

# ============================================================
# Auth Endpoints (Issue 89)
# ============================================================

@router.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login(request: LoginRequest, user_repo = Depends(get_user_repository)):
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
# Access Request Endpoints (Issue 91)
# ============================================================

@router.post("/requests", status_code=status.HTTP_201_CREATED, response_model=AccessRequestResponse, tags=["Access Requests"])
def create_access_request(
    payload: CreateAccessRequestDTO,
    current_user: User = Depends(require_any_role([UserRole.EMPLOYEE, UserRole.MANAGER, UserRole.SECURITY_REVIEWER, UserRole.IT_ADMIN])),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    req = use_cases.create_request(payload, current_user)
    return AccessRequestResponse(id=str(req.id), requester_id=req.requester_id, target_system=req.target_system, access_level=req.access_level.value, status=req.status.value, created_at=req.created_at)

@router.get("/requests", response_model=List[AccessRequestResponse], tags=["Access Requests"])
def list_requests(
    current_user: User = Depends(get_current_user),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    return [AccessRequestResponse(id=str(r.id), requester_id=r.requester_id, target_system=r.target_system, access_level=r.access_level.value, status=r.status.value, created_at=r.created_at) for r in use_cases.repo.get_all()]

@router.get("/requests/{request_id}", response_model=AccessRequestResponse, tags=["Access Requests"])
def get_request_detail(
    request_id: str,
    current_user: User = Depends(get_current_user),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    r = use_cases.get_request(request_id)
    return AccessRequestResponse(id=str(r.id), requester_id=r.requester_id, target_system=r.target_system, access_level=r.access_level.value, status=r.status.value, created_at=r.created_at)

@router.post("/requests/{request_id}/approve", response_model=AccessRequestResponse, tags=["Access Requests"])
def approve_request(
    request_id: str,
    current_user: User = Depends(require_any_role([UserRole.MANAGER, UserRole.SECURITY_REVIEWER])),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    r = use_cases.approve_request(request_id, current_user)
    return AccessRequestResponse(id=str(r.id), requester_id=r.requester_id, target_system=r.target_system, access_level=r.access_level.value, status=r.status.value, created_at=r.created_at)

@router.post("/requests/{request_id}/reject", response_model=AccessRequestResponse, tags=["Access Requests"])
def reject_request(
    request_id: str,
    payload: ActionReasonDTO,
    current_user: User = Depends(require_any_role([UserRole.MANAGER, UserRole.SECURITY_REVIEWER])),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    r = use_cases.reject_request(request_id, current_user, payload.reason)
    return AccessRequestResponse(id=str(r.id), requester_id=r.requester_id, target_system=r.target_system, access_level=r.access_level.value, status=r.status.value, created_at=r.created_at)

@router.post("/requests/{request_id}/provision", response_model=AccessRequestResponse, tags=["Access Requests"])
def provision_request(
    request_id: str,
    current_user: User = Depends(require_role(UserRole.IT_ADMIN)),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    r = use_cases.provision_request(request_id, current_user)
    return AccessRequestResponse(id=str(r.id), requester_id=r.requester_id, target_system=r.target_system, access_level=r.access_level.value, status=r.status.value, created_at=r.created_at)

# ============================================================
# Utility Endpoints (Mocks)
# ============================================================

@router.get("/notifications", response_model=List[NotificationResponse], tags=["Utility"])
def get_notifications(current_user: User = Depends(get_current_user)):
    return []

@router.get("/audit-log", response_model=List[AuditLogResponse], tags=["Utility"])
def get_audit_log(current_user: User = Depends(require_role(UserRole.SYSTEM_ADMIN))):
    return []