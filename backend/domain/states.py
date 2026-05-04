"""
State Pattern para el ciclo de vida de una solicitud de acceso.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from domain.enums import RequestStatus, UserRole
from domain.exceptions import (
    InvalidStateTransitionError,
    SelfApprovalError,
    RejectedRequestError,
    UnauthorizedError,
)

if TYPE_CHECKING:
    from domain.entities import AccessRequest, User


# ============================================================
# Clase abstracta del State
# ============================================================

class RequestState(ABC):
    """Clase abstracta que define las acciones posibles según el estado."""

    @abstractmethod
    def submit(self, request: AccessRequest) -> None:
        """Enviar la solicitud para revisión."""
        pass

    @abstractmethod
    def approve(self, request: AccessRequest, reviewer: User) -> None:
        """Aprobar la solicitud en el paso actual."""
        pass

    @abstractmethod
    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        """Rechazar la solicitud."""
        pass

    @abstractmethod
    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        """Solicitar cambios al solicitante."""
        pass

    @abstractmethod
    def cancel(self, request: AccessRequest) -> None:
        """Cancelar la solicitud."""
        pass

    @abstractmethod
    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        """Completar el provisioning del acceso."""
        pass
    
    def finalize_approval(self, request: AccessRequest) -> None:
        """
        Pasar la solicitud a READY_FOR_PROVISIONING.
        Solo aplica en APPROVED. Por defecto lanza error.
        """
        raise InvalidStateTransitionError(
            f"finalize_approval no es válido en el estado {request.status.value}"
        )
    @abstractmethod
    def return_to_draft(self, request: AccessRequest) -> None:
        """Volver a DRAFT para editar la solicitud (cuando se solicitaron cambios)."""
        pass


# ============================================================
# Estados concretos
# ============================================================

class DraftState(RequestState):
    """
    Estado: DRAFT
    El empleado está creando la solicitud. Puede enviarla o cancelarla.
    """

    def submit(self, request: AccessRequest) -> None:
        request._transition_to(RequestStatus.SUBMITTED)

    def approve(self, request: AccessRequest, reviewer: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede aprobar: la solicitud aún no ha sido enviada."
        )

    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        raise InvalidStateTransitionError(
            "No se puede rechazar: la solicitud aún no ha sido enviada."
        )

    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        raise InvalidStateTransitionError(
            "No se pueden solicitar cambios: la solicitud aún no ha sido enviada."
        )

    def cancel(self, request: AccessRequest) -> None:
        request._transition_to(RequestStatus.CANCELLED)

    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede completar provisioning: la solicitud no ha sido aprobada."
        )
    def return_to_draft(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
        f"No se puede volver a DRAFT en el estado {request.status.value}"
    )


class SubmittedState(RequestState):
    """
    Estado: SUBMITTED
    La solicitud fue enviada. El sistema la mueve automáticamente a MANAGER_REVIEW.
    Solo se puede cancelar.
    """

    def submit(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue enviada."
        )

    def approve(self, request: AccessRequest, reviewer: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede aprobar directamente desde SUBMITTED. "
            "La solicitud debe pasar primero a MANAGER_REVIEW."
        )

    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        raise InvalidStateTransitionError(
            "No se puede rechazar directamente desde SUBMITTED."
        )

    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        raise InvalidStateTransitionError(
            "No se pueden solicitar cambios directamente desde SUBMITTED."
        )

    def cancel(self, request: AccessRequest) -> None:
        request._transition_to(RequestStatus.CANCELLED)

    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede completar provisioning: la solicitud no ha sido aprobada."
        )
    def return_to_draft(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
        f"No se puede volver a DRAFT en el estado {request.status.value}"
    )


class ManagerReviewState(RequestState):
    """
    Estado: MANAGER_REVIEW
    El Manager debe aprobar, rechazar o solicitar cambios.
    Si aprueba y NO requiere Security, pasa a APPROVED.
    Si aprueba y SÍ requiere Security, pasa a SECURITY_REVIEW.
    """

    def submit(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya está en revisión."
        )

    def approve(self, request: AccessRequest, reviewer: User) -> None:
        # Validar que el revisor sea Manager (o System Admin)
        if reviewer.role not in (UserRole.MANAGER, UserRole.SYSTEM_ADMIN):
            raise UnauthorizedError("Solo un Manager puede aprobar en este paso.")

        # Validar que no se auto-apruebe
        if reviewer.id == request.requester_id:
            raise SelfApprovalError("El solicitante no puede aprobar su propia solicitud.")

        # Determinar siguiente estado
        if request.requires_security_review():
            request._transition_to(RequestStatus.SECURITY_REVIEW)
        else:
            request._transition_to(RequestStatus.APPROVED)

    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        if reviewer.role not in (UserRole.MANAGER, UserRole.SYSTEM_ADMIN):
            raise UnauthorizedError("Solo un Manager puede rechazar en este paso.")
        request.rejection_reason = reason
        request._transition_to(RequestStatus.REJECTED)

    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        if reviewer.role not in (UserRole.MANAGER, UserRole.SYSTEM_ADMIN):
            raise UnauthorizedError("Solo un Manager puede solicitar cambios en este paso.")
        request.changes_requested_by = reviewer.id
        request.changes_requested_comment = comment
        request._transition_to(RequestStatus.CHANGES_REQUESTED)

    def cancel(self, request: AccessRequest) -> None:
        request._transition_to(RequestStatus.CANCELLED)

    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede completar provisioning: la solicitud no ha sido aprobada."
        )

    def return_to_draft(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            f"No se puede volver a DRAFT en el estado {request.status.value}"
        )


class SecurityReviewState(RequestState):
    """
    Estado: SECURITY_REVIEW
    El Security Reviewer debe aprobar o rechazar.
    Solo se llega aquí si la solicitud es ADMIN o a base productiva.
    """

    def submit(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya está en revisión de seguridad."
        )

    def approve(self, request: AccessRequest, reviewer: User) -> None:
        if reviewer.role not in (UserRole.SECURITY_REVIEWER, UserRole.SYSTEM_ADMIN):
            raise UnauthorizedError("Solo un Security Reviewer puede aprobar en este paso.")
        request._transition_to(RequestStatus.APPROVED)

    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        if reviewer.role not in (UserRole.SECURITY_REVIEWER, UserRole.SYSTEM_ADMIN):
            raise UnauthorizedError("Solo un Security Reviewer puede rechazar en este paso.")
        request.rejection_reason = reason
        request._transition_to(RequestStatus.REJECTED)

    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        if reviewer.role not in (UserRole.SECURITY_REVIEWER, UserRole.SYSTEM_ADMIN):
            raise UnauthorizedError("Solo un Security Reviewer puede solicitar cambios en este paso.")
        request.changes_requested_by = reviewer.id
        request.changes_requested_comment = comment
        request._transition_to(RequestStatus.CHANGES_REQUESTED)

    def cancel(self, request: AccessRequest) -> None:
        request._transition_to(RequestStatus.CANCELLED)

    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede completar provisioning: la solicitud no ha sido aprobada."
        )
    def return_to_draft(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
        f"No se puede volver a DRAFT en el estado {request.status.value}"
    )


class ApprovedState(RequestState):
    """
    Estado: APPROVED
    La solicitud fue aprobada por todos los revisores requeridos.
    La capa de aplicación (servicio) debe llamar a finalize_approval() 
    para pasar a READY_FOR_PROVISIONING.
    """

    def submit(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue aprobada."
        )

    def approve(self, request: AccessRequest, reviewer: User) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue aprobada."
        )

    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        raise InvalidStateTransitionError(
            "No se puede rechazar una solicitud ya aprobada."
        )

    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        raise InvalidStateTransitionError(
            "No se pueden solicitar cambios: la solicitud ya fue aprobada."
        )

    def cancel(self, request: AccessRequest) -> None:
        request._transition_to(RequestStatus.CANCELLED)

    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        raise InvalidStateTransitionError(
            "La solicitud debe pasar primero a READY_FOR_PROVISIONING."
        )
    def finalize_approval(self, request: AccessRequest) -> None:
        """
        Pasar la solicitud a READY_FOR_PROVISIONING.
        Este método debe ser llamado por la capa de aplicación (servicio)
        después de que la solicitud llegue al estado APPROVED.
        """
        request._transition_to(RequestStatus.READY_FOR_PROVISIONING)
    def return_to_draft(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
        f"No se puede volver a DRAFT en el estado {request.status.value}"
    )

class ReadyForProvisioningState(RequestState):
    """
    Estado: READY_FOR_PROVISIONING
    Solo IT Admin puede completar el provisioning.
    """

    def submit(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "La solicitud está lista para provisioning."
        )

    def approve(self, request: AccessRequest, reviewer: User) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue aprobada. Debe completarse el provisioning."
        )

    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        raise InvalidStateTransitionError(
            "No se puede rechazar: la solicitud ya fue aprobada."
        )

    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        raise InvalidStateTransitionError(
            "No se pueden solicitar cambios: la solicitud ya fue aprobada."
        )

    def cancel(self, request: AccessRequest) -> None:
        request._transition_to(RequestStatus.CANCELLED)

    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        if it_admin.role not in (UserRole.IT_ADMIN, UserRole.SYSTEM_ADMIN):
            raise UnauthorizedError("Solo IT Admin puede completar el provisioning.")
        request.provisioned_by = it_admin.id
        request._transition_to(RequestStatus.COMPLETED)
    def return_to_draft(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
        f"No se puede volver a DRAFT en el estado {request.status.value}"
    )

class CompletedState(RequestState):
    """
    Estado: COMPLETED
    Estado final. El acceso fue provisionado.
    """

    def submit(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue completada."
        )

    def approve(self, request: AccessRequest, reviewer: User) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue completada."
        )

    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue completada."
        )

    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue completada."
        )

    def cancel(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "No se puede cancelar una solicitud completada."
        )

    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue completada."
        )
    def return_to_draft(self, request: AccessRequest) -> None:
     raise InvalidStateTransitionError(
        f"No se puede volver a DRAFT en el estado {request.status.value}"
    )


class RejectedState(RequestState):
    """
    Estado: REJECTED
    Estado final. No se puede modificar. El solicitante debe crear una nueva.
    """

    def submit(self, request: AccessRequest) -> None:
        raise RejectedRequestError(
            "Una solicitud rechazada no puede volver a enviarse. Debe crear una nueva."
        )

    def approve(self, request: AccessRequest, reviewer: User) -> None:
        raise RejectedRequestError(
            "Una solicitud rechazada no puede aprobarse. Debe crear una nueva."
        )

    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue rechazada."
        )

    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        raise RejectedRequestError(
            "No se pueden solicitar cambios: la solicitud fue rechazada."
        )

    def cancel(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "No se puede cancelar una solicitud ya rechazada."
        )

    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede completar provisioning: la solicitud fue rechazada."
        )
    def return_to_draft(self, request: AccessRequest) -> None:
     raise InvalidStateTransitionError(
        f"No se puede volver a DRAFT en el estado {request.status.value}"
    )


class CancelledState(RequestState):
    """
    Estado: CANCELLED
    Estado final. El solicitante canceló la solicitud.
    """

    def submit(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "No se puede enviar una solicitud cancelada."
        )

    def approve(self, request: AccessRequest, reviewer: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede aprobar una solicitud cancelada."
        )

    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        raise InvalidStateTransitionError(
            "No se puede rechazar una solicitud cancelada."
        )

    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        raise InvalidStateTransitionError(
            "No se pueden solicitar cambios: la solicitud fue cancelada."
        )

    def cancel(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "La solicitud ya fue cancelada."
        )

    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede completar provisioning: la solicitud fue cancelada."
        )
    def return_to_draft(self, request: AccessRequest) -> None:
     raise InvalidStateTransitionError(
        f"No se puede volver a DRAFT en el estado {request.status.value}"
    )


class ChangesRequestedState(RequestState):
    """
    Estado: CHANGES_REQUESTED
    Un revisor solicitó cambios. El solicitante debe editar y reenviar.
    Vuelve a DRAFT.
    """

    def submit(self, request: AccessRequest) -> None:
        raise InvalidStateTransitionError(
            "La solicitud tiene cambios solicitados. Debe volver a DRAFT primero."
        )

    def approve(self, request: AccessRequest, reviewer: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede aprobar: hay cambios solicitados pendientes."
        )

    def reject(self, request: AccessRequest, reviewer: User, reason: str) -> None:
        raise InvalidStateTransitionError(
            "No se puede rechazar: hay cambios solicitados pendientes."
        )

    def request_changes(self, request: AccessRequest, reviewer: User, comment: str) -> None:
        raise InvalidStateTransitionError(
            "Ya se solicitaron cambios. El solicitante debe atenderlos primero."
        )

    def cancel(self, request: AccessRequest) -> None:
        request._transition_to(RequestStatus.CANCELLED)

    def complete_provisioning(self, request: AccessRequest, it_admin: User) -> None:
        raise InvalidStateTransitionError(
            "No se puede completar provisioning: hay cambios solicitados pendientes."
        )
    
    def return_to_draft(self, request: AccessRequest) -> None:
     request._transition_to(RequestStatus.DRAFT)

# ============================================================
# Factory para crear el estado según el enum
# ============================================================

def create_state_from_status(status: RequestStatus, request: AccessRequest) -> RequestState:
    """
    Fábrica que retorna la instancia del estado correcto según el enum.
    Permite lazy loading del estado.
    """
    states = {
        RequestStatus.DRAFT: DraftState,
        RequestStatus.SUBMITTED: SubmittedState,
        RequestStatus.MANAGER_REVIEW: ManagerReviewState,
        RequestStatus.SECURITY_REVIEW: SecurityReviewState,
        RequestStatus.APPROVED: ApprovedState,
        RequestStatus.READY_FOR_PROVISIONING: ReadyForProvisioningState,
        RequestStatus.COMPLETED: CompletedState,
        RequestStatus.REJECTED: RejectedState,
        RequestStatus.CANCELLED: CancelledState,
        RequestStatus.CHANGES_REQUESTED: ChangesRequestedState,
    }

    state_class = states.get(status)
    if state_class is None:
        raise ValueError(f"Estado desconocido: {status}")

    return state_class()