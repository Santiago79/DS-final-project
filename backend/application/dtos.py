from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from domain.enums import AccessLevel, SystemType

# --- Auth DTOs ---

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

# --- Access Request DTOs ---
class CreateAccessRequestDTO(BaseModel):
    target_system: str
    access_level: AccessLevel
    justification: str
    system_type: SystemType = SystemType.OTHER
    expiration_date: Optional[date] = None
    manager_id: Optional[str] = None

class ActionReasonDTO(BaseModel):
    reason: str

class AccessRequestResponse(BaseModel):
    id: str
    requester_id: str
    target_system: str
    access_level: str
    justification: Optional[str] = None
    system_type: Optional[str] = None
    expiration_date: Optional[date] = None
    status: str
    rejection_reason: Optional[str] = None
    changes_requested_comment: Optional[str] = None
    created_at: datetime

# --- Utility DTOs ---
class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    status: str
    request_id: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None

class AuditLogResponse(BaseModel):
    id: int
    user_id: str
    request_id: Optional[str] = None
    action: str
    details: str
    created_at: datetime