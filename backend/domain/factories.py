from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from domain.entities import AccessRequest
from domain.enums import AccessLevel, SystemType, UserRole
from domain.exceptions import ExpirationRequiredError


# ============================================================
# AccessRequest Factory
# ============================================================

class AccessRequestFactory:
    """
    Fábrica para encapsular la creación de solicitudes de acceso.
    Aplica validaciones de negocio previas a la instanciación.
    """
    
    @staticmethod
    def create(
        requester_id: str,
        requester_name: str,
        target_system: str,
        access_level: AccessLevel,
        justification: str,
        system_type: SystemType = SystemType.OTHER,
        expiration_date: Optional[date] = None,
        manager_id: Optional[str] = None
    ) -> AccessRequest:
        
        if access_level == AccessLevel.ADMIN and expiration_date is None:
            raise ExpirationRequiredError(
                "Los accesos de nivel ADMIN requieren una fecha de expiración obligatoria."
            )
            
        return AccessRequest(
            requester_id=requester_id,
            requester_name=requester_name,
            target_system=target_system,
            access_level=access_level,
            justification=justification,
            system_type=system_type,
            expiration_date=expiration_date,
            manager_id=manager_id
        )


# ============================================================
# Approval Steps
# ============================================================

class ApprovalStep(ABC):
    """Objeto que representa un paso individual en el pipeline de aprobación."""
    @abstractmethod
    def get_role(self) -> UserRole:
        pass
        
    @abstractmethod
    def get_step_name(self) -> str:
        pass


class ManagerApprovalStep(ApprovalStep):
    def get_role(self) -> UserRole:
        return UserRole.MANAGER
        
    def get_step_name(self) -> str:
        return "MANAGER_REVIEW"


class SecurityApprovalStep(ApprovalStep):
    def get_role(self) -> UserRole:
        return UserRole.SECURITY_REVIEWER
        
    def get_step_name(self) -> str:
        return "SECURITY_REVIEW"


# ============================================================
# Approval Flow Factories (Abstract Factory Pattern)
# ============================================================

class ApprovalFlowFactory(ABC):
    """
    Abstract Factory para crear pipelines de aprobación.
    Devuelve una lista ordenada de objetos ApprovalStep.
    """
    @abstractmethod
    def create_approval_pipeline(self) -> List[ApprovalStep]:
        pass


class StandardApprovalFlowFactory(ApprovalFlowFactory):
    """Flujo estándar: Solo requiere la aprobación del Manager directo."""
    def create_approval_pipeline(self) -> List[ApprovalStep]:
        return [ManagerApprovalStep()]


class AdminApprovalFlowFactory(ApprovalFlowFactory):
    """Flujo Admin: Requiere primero al Manager, luego al equipo de Seguridad."""
    def create_approval_pipeline(self) -> List[ApprovalStep]:
        return [ManagerApprovalStep(), SecurityApprovalStep()]


class ProductiveDatabaseFlowFactory(ApprovalFlowFactory):
    """
    Flujo para Bases de Datos Productivas: 
    Requiere primero a Seguridad (riesgo inmediato) y luego al Manager.
    """
    def create_approval_pipeline(self) -> List[ApprovalStep]:
        return [SecurityApprovalStep(), ManagerApprovalStep()]
