from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from application.dtos import (
    TokenResponse, CreateAccessRequestDTO, 
    AccessRequestResponse, ActionReasonDTO, 
    NotificationResponse, AuditLogResponse
)
from infrastructure.auth_provider import AuthProvider
from api.dependencies import get_user_repository, get_current_user, get_access_request_use_cases
from api.guards import require_role, require_any_role
from domain.enums import UserRole
from domain.entities import User
from application.use_cases import AccessRequestUseCases

# Imports necesarios para los nuevos endpoints
from infrastructure.database import get_db
from infrastructure.postgres import PostgresNotificationRepository, PostgresAuditLogRepository

router = APIRouter(tags=["AccessFlow API"])

# Helper para mapear la respuesta
def map_to_response(req) -> AccessRequestResponse:
    return AccessRequestResponse(
        id=str(req.id),
        requester_id=req.requester_id,
        requester_name=req.requester_name,
        target_system=req.target_system,
        access_level=req.access_level.value,
        justification=req.justification,
        system_type=req.system_type.value,
        expiration_date=req.expiration_date,
        status=req.status.value,
        rejection_reason=req.rejection_reason,
        changes_requested_comment=req.changes_requested_comment,
        created_at=req.created_at
    )

# ============================================================
# Auth Endpoints
# ============================================================

@router.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    user_repo = Depends(get_user_repository)
):
    user = user_repo.get_by_email(form_data.username)
    
    if not user or not AuthProvider.verify_password(form_data.password, user.hashed_password):
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
# Access Request Endpoints
# ============================================================

@router.post("/requests", status_code=status.HTTP_201_CREATED, response_model=AccessRequestResponse, tags=["Access Requests"])
def create_access_request(
    payload: CreateAccessRequestDTO,
    current_user: User = Depends(require_any_role([UserRole.EMPLOYEE, UserRole.MANAGER, UserRole.SECURITY_REVIEWER, UserRole.IT_ADMIN])),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    req = use_cases.create_request(payload, current_user)
    return map_to_response(req)

@router.get("/requests", response_model=List[AccessRequestResponse], tags=["Access Requests"])
def list_requests(
    current_user: User = Depends(get_current_user),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    requests = use_cases.list_requests(current_user)
    return [map_to_response(r) for r in requests]

@router.get("/requests/{request_id}", response_model=AccessRequestResponse, tags=["Access Requests"])
def get_request_detail(
    request_id: str,
    current_user: User = Depends(get_current_user),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    req = use_cases.get_request(request_id)
    return map_to_response(req)

@router.post("/requests/{request_id}/approve", response_model=AccessRequestResponse, tags=["Access Requests"])
def approve_request(
    request_id: str,
    current_user: User = Depends(require_any_role([UserRole.MANAGER, UserRole.SECURITY_REVIEWER])),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    req = use_cases.approve_request(request_id, current_user)
    return map_to_response(req)

@router.post("/requests/{request_id}/reject", response_model=AccessRequestResponse, tags=["Access Requests"])
def reject_request(
    request_id: str,
    payload: ActionReasonDTO,
    current_user: User = Depends(require_any_role([UserRole.MANAGER, UserRole.SECURITY_REVIEWER])),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    req = use_cases.reject_request(request_id, current_user, payload.reason)
    return map_to_response(req)

@router.post("/requests/{request_id}/request-changes", response_model=AccessRequestResponse, tags=["Access Requests"])
def request_changes(
    request_id: str,
    payload: ActionReasonDTO,
    current_user: User = Depends(require_any_role([UserRole.MANAGER, UserRole.SECURITY_REVIEWER])),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    req = use_cases.request_changes(request_id, current_user, payload.reason)
    return map_to_response(req)

@router.post("/requests/{request_id}/cancel", response_model=AccessRequestResponse, tags=["Access Requests"])
def cancel_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    req = use_cases.cancel_request(request_id, current_user)
    return map_to_response(req)

@router.post("/requests/{request_id}/provision", response_model=AccessRequestResponse, tags=["Access Requests"])
def provision_request(
    request_id: str,
    current_user: User = Depends(require_any_role([UserRole.IT_ADMIN, UserRole.SYSTEM_ADMIN])),
    use_cases: AccessRequestUseCases = Depends(get_access_request_use_cases)
):
    req = use_cases.provision_request(request_id, current_user)
    return map_to_response(req)

# ============================================================
# Utility Endpoints (Notificaciones y Auditoría Reales)
# ============================================================

@router.get("/notifications", response_model=List[NotificationResponse], tags=["Utility"])
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = PostgresNotificationRepository(db)
    return repo.get_by_user(current_user.id)

@router.put("/notifications/{notification_id}/read", status_code=status.HTTP_200_OK, tags=["Utility"])
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = PostgresNotificationRepository(db)
    repo.mark_as_read(notification_id)
    return {"message": "Notification marked as read"}

@router.get("/requests/{request_id}/audit-log", response_model=List[AuditLogResponse], tags=["Utility"])
def get_request_audit_log(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # In a real app we might want to check if the user is authorized to view this request's audit log
    repo = PostgresAuditLogRepository(db)
    return repo.get_by_request(request_id)

@router.get("/audit-log", response_model=List[AuditLogResponse], tags=["Utility"])
def get_audit_log(
    current_user: User = Depends(require_role(UserRole.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    repo = PostgresAuditLogRepository(db)
    return repo.get_all()