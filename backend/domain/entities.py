from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4

from domain.exceptions import (
    ExpirationRequiredError,
    RejectedRequestError,
    SelfApprovalError,
    UnauthorizedError,
    ValidationError,
)
from domain.enums import (
    AccessLevel,
    NotificationStatus,
    RequestStatus,
    SystemType,
    UserRole,
)
from domain.states import RequestState, create_state_from_status


# ============================================================
# User
# ============================================================

@dataclass
class User:
    """Usuario del sistema con rol asignado."""
    name: str
    email: str
    hashed_password: str
    role: UserRole
    id: str = field(default_factory=lambda: str(uuid4()))
    manager_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.name or len(self.name.strip()) < 2:
            raise ValidationError("El nombre del usuario debe tener al menos 2 caracteres.")
        if "@" not in self.email:
            raise ValidationError("El formato del email es inválido.")
        if not isinstance(self.role, UserRole):
            raise ValidationError(f"Rol inválido: {self.role}")

    def is_manager_of(self, employee: "User") -> bool:
        """Verifica si este usuario es el manager directo del empleado."""
        return employee.manager_id == self.id

    def can_approve_as(self, required_role: UserRole) -> bool:
        """Verifica si este usuario tiene el rol requerido para aprobar."""
        return self.role in (required_role, UserRole.SYSTEM_ADMIN)


# ============================================================
# AccessRequest (entidad principal del caso)
# ============================================================

@dataclass
class AccessRequest:
    """Solicitud de acceso a una herramienta interna."""
    requester_id: str
    requester_name: str
    target_system: str
    access_level: AccessLevel
    justification: str
    id: str = field(default_factory=lambda: str(uuid4()))
    manager_id: Optional[str] = None
    system_type: SystemType = SystemType.OTHER
    expiration_date: Optional[date] = None
    _status: RequestStatus = field(default=RequestStatus.DRAFT)
    rejection_reason: Optional[str] = None
    changes_requested_by: Optional[str] = None
    changes_requested_comment: Optional[str] = None
    provisioned_by: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _state: Optional[RequestState] = field(default=None, init=False, repr=False)
    
    def __post_init__(self) -> None:
        # Validaciones básicas
        if not self.requester_id:
            raise ValidationError("El solicitante es requerido.")
        if not self.requester_name or len(self.requester_name.strip()) < 2:
            raise ValidationError("El nombre del solicitante debe tener al menos 2 caracteres.")
        if not self.target_system or len(self.target_system.strip()) < 2:
            raise ValidationError("El sistema destino debe tener al menos 2 caracteres.")
        if not isinstance(self.access_level, AccessLevel):
            raise ValidationError(f"Nivel de acceso inválido: {self.access_level}")
        if not self.justification or len(self.justification.strip()) < 5:
            raise ValidationError("La justificación debe tener al menos 5 caracteres.")

        # Regla de negocio: ADMIN requiere fecha de expiración obligatoria
        if self.access_level == AccessLevel.ADMIN and self.expiration_date is None:
            raise ExpirationRequiredError(
                "Los accesos de nivel ADMIN requieren una fecha de expiración obligatoria."
            )

        # Validar que la fecha de expiración sea futura
        if self.expiration_date and self.expiration_date <= date.today():
            raise ValidationError("La fecha de expiración debe ser una fecha futura.")

    # ============================================================
    # Propiedades
    # ============================================================

    @property
    def status(self) -> RequestStatus:
        """Retorna el estado actual de la solicitud."""
        return self._status
 
    @property
    def state(self) -> RequestState:
        """Retorna el estado lógico de la solicitud."""
        if self._state is None:
            self._state = create_state_from_status(self._status, self)
        return self._state


    # ============================================================
    # Validaciones de reglas de negocio
    # ============================================================

    def validate_approval(self, approver: "User") -> None:
        """
        Valida que la aprobación sea válida según reglas de negocio.
        - El solicitante no puede aprobar su propia solicitud.
        - Una solicitud rechazada no puede volver a aprobarse.
        """
        if approver.id == self.requester_id:
            raise SelfApprovalError("El solicitante no puede aprobar su propia solicitud.")
        if self._status == RequestStatus.REJECTED:
            raise RejectedRequestError(
                "Una solicitud rechazada no puede volver a aprobarse. Debe crear una nueva solicitud."
            )

    def validate_provisioning(self, approver: "User") -> None:
        """
        Valida que solo IT Admin pueda completar el provisioning.
        """
        if approver.role not in (UserRole.IT_ADMIN, UserRole.SYSTEM_ADMIN):
            raise UnauthorizedError("Solo IT Admin puede completar el provisioning.")
        if self._status != RequestStatus.READY_FOR_PROVISIONING:
            raise ValidationError(
                f"La solicitud debe estar en READY_FOR_PROVISIONING para completarse. "
                f"Estado actual: {self._status.value}"
            )

    # ============================================================
    # Reglas de negocio: expiración
    # ============================================================

    def is_expiration_required(self) -> bool:
        """Accesos ADMIN requieren expiración obligatoria."""
        return self.access_level == AccessLevel.ADMIN

    def is_expired(self) -> bool:
        """Verifica si la solicitud ya expiró."""
        if self.expiration_date is None:
            return False
        return self.expiration_date < date.today()

    def days_until_expiration(self) -> Optional[int]:
        """Retorna los días restantes hasta la expiración, o None si no tiene fecha."""
        if self.expiration_date is None:
            return None
        delta = self.expiration_date - date.today()
        return delta.days

    # ============================================================
    # Reglas de negocio: flujo de aprobación
    # ============================================================

    def requires_security_review(self) -> bool:
        """
        Determina si la solicitud requiere revisión de Security Reviewer.
        Reglas:
        - Accesos ADMIN siempre requieren Security.
        - Accesos a bases de datos productivas siempre requieren Security.
        """
        if self.access_level == AccessLevel.ADMIN:
            return True
        if self.system_type == SystemType.PRODUCTIVE_DATABASE:
            return True
        return False

    # ============================================================
    # Cambio de estado 
    # ============================================================

    def _transition_to(self, new_status: RequestStatus) -> None:
        """Método interno para cambiar el estado de la solicitud."""
        self._status = new_status
        self._state = None  # Invalida el estado lógico para que se regenere
        self.updated_at = datetime.now(timezone.utc)

    def submit(self) -> None:
        self.state.submit(self)
        self.updated_at = datetime.now(timezone.utc)

    def approve(self, reviewer: User) -> None:
        self.state.approve(self, reviewer)
        self.updated_at = datetime.now(timezone.utc)

    def reject(self, reviewer: User, reason: str) -> None:
        self.state.reject(self, reviewer, reason)
        self.updated_at = datetime.now(timezone.utc)

    def request_changes(self, reviewer: User, comment: str) -> None:
        self.state.request_changes(self, reviewer, comment)
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        self.state.cancel(self)
        self.updated_at = datetime.now(timezone.utc)

    def complete_provisioning(self, it_admin: User) -> None:
        self.state.complete_provisioning(self, it_admin)
        self.updated_at = datetime.now(timezone.utc)

    def finalize_approval(self) -> None:
        """Delega el paso a READY_FOR_PROVISIONING al estado actual."""
        self.state.finalize_approval(self)
        self.updated_at = datetime.now(timezone.utc)

    def return_to_draft(self) -> None:
        """Devuelve la solicitud a DRAFT para edición."""
        self.state.return_to_draft(self)
        self.updated_at = datetime.now(timezone.utc)

# ============================================================
# AuditLog
# ============================================================

@dataclass
class AuditLog:
    """Registro de auditoría para trazabilidad completa."""
    event_type: str
    request_id: str
    actor_id: str
    actor_name: str
    details: str
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.event_type:
            raise ValidationError("El tipo de evento es requerido.")
        if not self.request_id:
            raise ValidationError("El ID de la solicitud es requerido.")
        if not self.actor_id:
            raise ValidationError("El actor del evento es requerido.")


# ============================================================
# Notification
# ============================================================

@dataclass
class Notification:
    """Notificación generada por eventos del sistema."""
    recipient: str
    message: str
    event_type: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: NotificationStatus = field(default=NotificationStatus.PENDING)
    request_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.recipient:
            raise ValidationError("El destinatario de la notificación es requerido.")
        if not self.message or len(self.message.strip()) < 1:
            raise ValidationError("El contenido de la notificación no puede estar vacío.")
        if not self.event_type:
            raise ValidationError("El tipo de evento es requerido.")

    def mark_as_read(self) -> None:
        """Marca la notificación como leída."""
        self.read_at = datetime.now(timezone.utc)
        self.status = NotificationStatus.READ
