"""
Definición de eventos del dominio para el patrón Observer.
Los eventos se publican cuando ocurren cambios importantes en el negocio.
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities import AccessRequest


@dataclass(kw_only=True)
class Evento(ABC):
    """Clase base abstracta para todos los eventos del dominio."""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================
# Eventos de AccessRequest
# ============================================================

@dataclass(kw_only=True)
class AccessRequestCreatedEvent(Evento):
    """Evento: Una solicitud de acceso fue creada (estado DRAFT)."""
    request: "AccessRequest"


@dataclass(kw_only=True)
class AccessRequestSubmittedEvent(Evento):
    """Evento: La solicitud fue enviada para revisión."""
    request: "AccessRequest"


@dataclass(kw_only=True)
class ManagerApprovalRequiredEvent(Evento):
    """Evento: La solicitud requiere aprobación del Manager."""
    request: "AccessRequest"


@dataclass(kw_only=True)
class SecurityReviewRequiredEvent(Evento):
    """Evento: La solicitud requiere revisión de Security Reviewer."""
    request: "AccessRequest"


@dataclass(kw_only=True)
class AccessRequestApprovedEvent(Evento):
    """Evento: La solicitud fue aprobada."""
    request: "AccessRequest"
    approved_by: str  # user_id


@dataclass(kw_only=True)
class AccessRequestRejectedEvent(Evento):
    """Evento: La solicitud fue rechazada."""
    request: "AccessRequest"
    rejected_by: str  # user_id
    reason: str


@dataclass(kw_only=True)
class ChangesRequestedEvent(Evento):
    """Evento: Se solicitaron cambios en la solicitud."""
    request: "AccessRequest"
    requested_by: str  # user_id
    comment: str


@dataclass(kw_only=True)
class AccessProvisionedEvent(Evento):
    """Evento: El acceso fue provisionado por IT Admin."""
    request: "AccessRequest"
    provisioned_by: str  # user_id


@dataclass(kw_only=True)
class AccessExpiringSoonEvent(Evento):
    """Evento: Un acceso está próximo a expirar."""
    request: "AccessRequest"
    days_remaining: int