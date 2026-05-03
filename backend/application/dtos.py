from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from domain.enums import AccessLevel, SystemType

# --- Auth DTOs ---
class LoginRequest(BaseModel):
    email: str
    password: str

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
    status: str
    created_at: datetime

# --- Utility DTOs ---
class NotificationResponse(BaseModel):
    id: str
    message: str
    created_at: datetime

class AuditLogResponse(BaseModel):
    id: str
    action: str
    performed_by: str
    timestamp: datetime