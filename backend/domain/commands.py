"""
Implementación del patrón Command para las acciones del sistema.
Cada comando encapsula validaciones, cambio de estado y publicación de eventos.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from domain.events import (
    AccessRequestApprovedEvent,
    AccessRequestCreatedEvent,
    AccessRequestRejectedEvent,
    AccessRequestSubmittedEvent,
    AccessProvisionedEvent,
    ChangesRequestedEvent,
    ManagerApprovalRequiredEvent,
    SecurityReviewRequiredEvent,
)

if TYPE_CHECKING:
    from domain.entities import AccessRequest, User
    from domain.interfaces.event_bus import EventBus


# ============================================================
# Comando Abstracto
# ============================================================

class RequestCommand(ABC):
    """Clase abstracta para comandos sobre solicitudes de acceso."""

    def __init__(self, request: "AccessRequest", event_bus: "EventBus"):
        """
        Args:
            request: La solicitud de acceso sobre la que se ejecuta el comando
            event_bus: Bus de eventos para publicar los eventos resultantes
        """
        self.request = request
        self.event_bus = event_bus

    @abstractmethod
    def execute(self) -> None:
        """Ejecuta el comando: valida, cambia estado y publica evento."""
        pass


# ============================================================
# Comandos Concretos
# ============================================================

class CreateRequestCommand(RequestCommand):
    """
    Comando para crear una nueva solicitud de acceso.
    La solicitud ya viene creada por la factory. Solo se publica el evento.
    """

    def execute(self) -> None:
        event = AccessRequestCreatedEvent(request=self.request)
        self.event_bus.publish(event)


class SubmitRequestCommand(RequestCommand):
    """
    Comando para enviar la solicitud a revisión.
    Transiciona de DRAFT a SUBMITTED.
    """

    def execute(self) -> None:
        self.request.submit()
        event = AccessRequestSubmittedEvent(request=self.request)
        self.event_bus.publish(event)
        manager_event = ManagerApprovalRequiredEvent(request=self.request)
        self.event_bus.publish(manager_event)


class ApproveRequestCommand(RequestCommand):
    """
    Comando para aprobar una solicitud en el paso actual.
    Valida que el aprobador no sea el solicitante.
    Determina si pasa a SECURITY_REVIEW o directamente a APPROVED.
    """

    def __init__(self, request: "AccessRequest", event_bus: "EventBus", reviewer: "User"):
        super().__init__(request, event_bus)
        self.reviewer = reviewer

    def execute(self) -> None:
        # Validar que no se auto-apruebe
        self.request.validate_approval(self.reviewer)

        # Ejecutar la transición de estado
        self.request.approve(self.reviewer)

        # Publicar evento según el nuevo estado
        if self.request.status.value == "SECURITY_REVIEW":
            event = SecurityReviewRequiredEvent(request=self.request)
        else:
            event = AccessRequestApprovedEvent(
                request=self.request,
                approved_by=self.reviewer.id
            )
        self.event_bus.publish(event)


class RejectRequestCommand(RequestCommand):
    """
    Comando para rechazar una solicitud.
    Cambia el estado a REJECTED (estado final, no se puede reabrir).
    """

    def __init__(
        self,
        request: "AccessRequest",
        event_bus: "EventBus",
        reviewer: "User",
        reason: str
    ):
        super().__init__(request, event_bus)
        self.reviewer = reviewer
        self.reason = reason

    def execute(self) -> None:
        self.request.reject(self.reviewer, self.reason)
        event = AccessRequestRejectedEvent(
            request=self.request,
            rejected_by=self.reviewer.id,
            reason=self.reason
        )
        self.event_bus.publish(event)


class RequestChangesCommand(RequestCommand):
    """
    Comando para solicitar cambios en la solicitud.
    Devuelve la solicitud a DRAFT para que el empleado la modifique.
    """

    def __init__(
        self,
        request: "AccessRequest",
        event_bus: "EventBus",
        reviewer: "User",
        comment: str
    ):
        super().__init__(request, event_bus)
        self.reviewer = reviewer
        self.comment = comment

    def execute(self) -> None:
        self.request.request_changes(self.reviewer, self.comment)
        event = ChangesRequestedEvent(
            request=self.request,
            requested_by=self.reviewer.id,
            comment=self.comment
        )
        self.event_bus.publish(event)


class ProvisionAccessCommand(RequestCommand):
    """
    Comando para completar el provisioning del acceso.
    Solo puede ser ejecutado por IT Admin.
    """

    def __init__(self, request: "AccessRequest", event_bus: "EventBus", it_admin: "User"):
        super().__init__(request, event_bus)
        self.it_admin = it_admin

    def execute(self) -> None:
        # Validar que solo IT Admin pueda ejecutar
        self.request.validate_provisioning(self.it_admin)

        # Ejecutar provisioning
        self.request.complete_provisioning(self.it_admin)

        event = AccessProvisionedEvent(
            request=self.request,
            provisioned_by=self.it_admin.id
        )
        self.event_bus.publish(event)


class CancelRequestCommand(RequestCommand):
    """
    Comando para cancelar una solicitud.
    Cambia el estado a CANCELLED (estado final).
    """

    def execute(self) -> None:
        self.request.cancel()
        # La cancelación no tiene un evento específico definido en el discovery,
        # pero puede publicarse si se requiere trazabilidad.
