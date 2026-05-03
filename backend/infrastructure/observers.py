"""
Event observers for domain events.

These observers react to domain events and perform side effects:
- NotificationObserver: Creates notifications for relevant users
- AuditLogObserver: Persists event details to audit log
"""

from typing import Optional

from domain.events import (
    Evento,
    AccessRequestCreatedEvent,
    AccessRequestSubmittedEvent,
    ManagerApprovalRequiredEvent,
    SecurityReviewRequiredEvent,
    AccessRequestApprovedEvent,
    AccessRequestRejectedEvent,
    ChangesRequestedEvent,
    AccessProvisionedEvent,
    AccessExpiringSoonEvent,
)
from domain.interfaces.observador_evento import ObservadorEvento
from infrastructure.postgres import (
    PostgresNotificationRepository,
    PostgresAuditLogRepository,
    PostgresUserRepository,
)
from sqlalchemy.orm import Session


# ============================================================
# Notification Observer
# ============================================================

class NotificationObserver(ObservadorEvento):
    """
    Observer that creates notifications based on domain events.
    
    Sends notifications to relevant users when important events occur.
    """

    def __init__(self, notification_repo: PostgresNotificationRepository, session: Session):
        """
        Initialize the notification observer.
        
        Args:
            notification_repo: Repository for creating notifications
            session: Database session for queries
        """
        self.notification_repo = notification_repo
        self.session = session

    def on_event(self, evento: Evento) -> None:
        """
        Process event and create notifications for relevant users.
        
        Args:
            evento: The domain event that occurred
        """
        if isinstance(evento, AccessRequestCreatedEvent):
            self._on_request_created(evento)
        elif isinstance(evento, AccessRequestSubmittedEvent):
            self._on_request_submitted(evento)
        elif isinstance(evento, ManagerApprovalRequiredEvent):
            self._on_manager_approval_required(evento)
        elif isinstance(evento, SecurityReviewRequiredEvent):
            self._on_security_review_required(evento)
        elif isinstance(evento, AccessRequestApprovedEvent):
            self._on_request_approved(evento)
        elif isinstance(evento, AccessRequestRejectedEvent):
            self._on_request_rejected(evento)
        elif isinstance(evento, ChangesRequestedEvent):
            self._on_changes_requested(evento)
        elif isinstance(evento, AccessProvisionedEvent):
            self._on_access_provisioned(evento)
        elif isinstance(evento, AccessExpiringSoonEvent):
            self._on_access_expiring_soon(evento)

    def _on_request_created(self, evento: AccessRequestCreatedEvent) -> None:
        """Notify manager and IT Admin when request is created."""
        request = evento.request
        
        # Notify manager
        if request.manager_id:
            self.notification_repo.add(
                user_id=request.manager_id,
                title="Nueva solicitud de acceso",
                message=f"El usuario {request.requester_name} solicita acceso a {request.target_system}",
                request_id=request.id,
            )
        
        # Notify IT Admin (would need to query for IT_ADMIN users, simplified for now)
        self.notification_repo.add(
            user_id="IT_ADMIN",  # Placeholder - would need to query actual IT admins
            title="Nueva solicitud de acceso creada",
            message=f"Solicitud #{request.id} creada para {request.requester_name}",
            request_id=request.id,
        )

    def _on_request_submitted(self, evento: AccessRequestSubmittedEvent) -> None:
        """Notify manager when request is submitted for review."""
        request = evento.request
        
        if request.manager_id:
            self.notification_repo.add(
                user_id=request.manager_id,
                title="Solicitud de acceso requiere tu aprobación",
                message=f"Solicitud de {request.requester_name} para {request.target_system}",
                request_id=request.id,
            )

    def _on_manager_approval_required(self, evento: ManagerApprovalRequiredEvent) -> None:
        """Notify manager when approval is required."""
        request = evento.request
        
        if request.manager_id:
            self.notification_repo.add(
                user_id=request.manager_id,
                title="Aprobación requerida",
                message=f"{request.requester_name} solicita {request.access_level.value} a {request.target_system}",
                request_id=request.id,
            )

    def _on_security_review_required(self, evento: SecurityReviewRequiredEvent) -> None:
        """Notify security reviewers when review is required."""
        request = evento.request
        
        # Notify security reviewer (placeholder - would query for actual security reviewers)
        self.notification_repo.add(
            user_id="SECURITY_REVIEWER",  # Placeholder
            title="Revisión de seguridad requerida",
            message=f"Solicitud de acceso {request.access_level.value} a {request.target_system}",
            request_id=request.id,
        )

    def _on_request_approved(self, evento: AccessRequestApprovedEvent) -> None:
        """Notify requester when request is approved."""
        request = evento.request
        
        self.notification_repo.add(
            user_id=request.requester_id,
            title="¡Solicitud aprobada!",
            message=f"Tu solicitud de acceso a {request.target_system} ha sido aprobada",
            request_id=request.id,
        )

    def _on_request_rejected(self, evento: AccessRequestRejectedEvent) -> None:
        """Notify requester when request is rejected."""
        request = evento.request
        
        self.notification_repo.add(
            user_id=request.requester_id,
            title="Solicitud rechazada",
            message=f"Tu solicitud fue rechazada. Motivo: {evento.reason}",
            request_id=request.id,
        )

    def _on_changes_requested(self, evento: ChangesRequestedEvent) -> None:
        """Notify requester when changes are requested."""
        request = evento.request
        
        self.notification_repo.add(
            user_id=request.requester_id,
            title="Se solicitan cambios",
            message=f"Cambios requeridos: {evento.comment}",
            request_id=request.id,
        )

    def _on_access_provisioned(self, evento: AccessProvisionedEvent) -> None:
        """Notify requester when access is provisioned."""
        request = evento.request
        
        self.notification_repo.add(
            user_id=request.requester_id,
            title="Acceso provisionado",
            message=f"Tu acceso a {request.target_system} está listo para usar",
            request_id=request.id,
        )

    def _on_access_expiring_soon(self, evento: AccessExpiringSoonEvent) -> None:
        """Notify requester when access is expiring soon."""
        request = evento.request
        
        self.notification_repo.add(
            user_id=request.requester_id,
            title="Acceso próximo a expirar",
            message=f"Tu acceso a {request.target_system} expira en {evento.days_remaining} días",
            request_id=request.id,
        )


# ============================================================
# Audit Log Observer
# ============================================================

class AuditLogObserver(ObservadorEvento):
    """
    Observer that persists domain events to the audit log.
    
    Creates an immutable record of all important domain events for compliance.
    """

    def __init__(self, audit_repo: PostgresAuditLogRepository):
        """
        Initialize the audit log observer.
        
        Args:
            audit_repo: Repository for persisting audit logs
        """
        self.audit_repo = audit_repo

    def on_event(self, evento: Evento) -> None:
        """
        Persist event details to audit log.
        
        Args:
            evento: The domain event that occurred
        """
        if isinstance(evento, AccessRequestCreatedEvent):
            self._log_request_created(evento)
        elif isinstance(evento, AccessRequestSubmittedEvent):
            self._log_request_submitted(evento)
        elif isinstance(evento, ManagerApprovalRequiredEvent):
            self._log_manager_approval_required(evento)
        elif isinstance(evento, SecurityReviewRequiredEvent):
            self._log_security_review_required(evento)
        elif isinstance(evento, AccessRequestApprovedEvent):
            self._log_request_approved(evento)
        elif isinstance(evento, AccessRequestRejectedEvent):
            self._log_request_rejected(evento)
        elif isinstance(evento, ChangesRequestedEvent):
            self._log_changes_requested(evento)
        elif isinstance(evento, AccessProvisionedEvent):
            self._log_access_provisioned(evento)
        elif isinstance(evento, AccessExpiringSoonEvent):
            self._log_access_expiring_soon(evento)

    def _log_request_created(self, evento: AccessRequestCreatedEvent) -> None:
        """Log when request is created."""
        request = evento.request
        self.audit_repo.add(
            user_id=request.requester_id,
            action="REQUEST_CREATED",
            request_id=request.id,
            details=f"Solicitud creada: {request.target_system} ({request.access_level.value})",
        )

    def _log_request_submitted(self, evento: AccessRequestSubmittedEvent) -> None:
        """Log when request is submitted."""
        request = evento.request
        self.audit_repo.add(
            user_id=request.requester_id,
            action="REQUEST_SUBMITTED",
            request_id=request.id,
            details=f"Solicitud enviada para revisión",
        )

    def _log_manager_approval_required(self, evento: ManagerApprovalRequiredEvent) -> None:
        """Log when manager approval is required."""
        request = evento.request
        self.audit_repo.add(
            user_id=request.manager_id or "SYSTEM",
            action="MANAGER_APPROVAL_REQUIRED",
            request_id=request.id,
            details=f"Aprobación de manager requerida",
        )

    def _log_security_review_required(self, evento: SecurityReviewRequiredEvent) -> None:
        """Log when security review is required."""
        request = evento.request
        self.audit_repo.add(
            user_id="SYSTEM",
            action="SECURITY_REVIEW_REQUIRED",
            request_id=request.id,
            details=f"Revisión de seguridad requerida para {request.target_system}",
        )

    def _log_request_approved(self, evento: AccessRequestApprovedEvent) -> None:
        """Log when request is approved."""
        request = evento.request
        self.audit_repo.add(
            user_id=evento.approved_by,
            action="REQUEST_APPROVED",
            request_id=request.id,
            details=f"Solicitud aprobada por {evento.approved_by}",
        )

    def _log_request_rejected(self, evento: AccessRequestRejectedEvent) -> None:
        """Log when request is rejected."""
        request = evento.request
        self.audit_repo.add(
            user_id=evento.rejected_by,
            action="REQUEST_REJECTED",
            request_id=request.id,
            details=f"Solicitud rechazada. Motivo: {evento.reason}",
        )

    def _log_changes_requested(self, evento: ChangesRequestedEvent) -> None:
        """Log when changes are requested."""
        request = evento.request
        self.audit_repo.add(
            user_id=evento.requested_by,
            action="CHANGES_REQUESTED",
            request_id=request.id,
            details=f"Cambios solicitados: {evento.comment}",
        )

    def _log_access_provisioned(self, evento: AccessProvisionedEvent) -> None:
        """Log when access is provisioned."""
        request = evento.request
        self.audit_repo.add(
            user_id=evento.provisioned_by,
            action="ACCESS_PROVISIONED",
            request_id=request.id,
            details=f"Acceso provisionado a {request.target_system}",
        )

    def _log_access_expiring_soon(self, evento: AccessExpiringSoonEvent) -> None:
        """Log when access is expiring soon."""
        request = evento.request
        self.audit_repo.add(
            user_id="SYSTEM",
            action="ACCESS_EXPIRING_SOON",
            request_id=request.id,
            details=f"Acceso expira en {evento.days_remaining} días",
        )
