from abc import ABC, abstractmethod
from typing import List

from domain.entities import AccessRequest
from domain.enums import AccessLevel, SystemType
from domain.factories import (
    AdminApprovalFlowFactory,
    ApprovalFlowFactory,
    ApprovalStep,
    ProductiveDatabaseFlowFactory,
    StandardApprovalFlowFactory,
)


# ============================================================
# Interfaz del Strategy
# ============================================================

class ApprovalPolicy(ABC):
    """
    Interfaz Strategy para determinar la política de aprobación.
    Define el contrato para generar el pipeline de pasos de revisión.
    """
    @abstractmethod
    def get_approval_pipeline(self) -> List[ApprovalStep]:
        """Retorna la lista de pasos requeridos para la aprobación."""
        pass


# ============================================================
# Estrategias Concretas
# ============================================================

class StandardApprovalPolicy(ApprovalPolicy):
    """Política para accesos básicos (READ/WRITE) en sistemas comunes."""
    def __init__(self, factory: ApprovalFlowFactory = StandardApprovalFlowFactory()):
        self.factory = factory

    def get_approval_pipeline(self) -> List[ApprovalStep]:
        return self.factory.create_approval_pipeline()


class AdminApprovalPolicy(ApprovalPolicy):
    """Política de alta seguridad para accesos ADMIN."""
    def __init__(self, factory: ApprovalFlowFactory = AdminApprovalFlowFactory()):
        self.factory = factory

    def get_approval_pipeline(self) -> List[ApprovalStep]:
        return self.factory.create_approval_pipeline()


class ProductiveDatabasePolicy(ApprovalPolicy):
    """Política crítica para cualquier acceso a bases de datos productivas."""
    def __init__(self, factory: ApprovalFlowFactory = ProductiveDatabaseFlowFactory()):
        self.factory = factory

    def get_approval_pipeline(self) -> List[ApprovalStep]:
        return self.factory.create_approval_pipeline()


# ============================================================
# Selector Automático (Context)
# ============================================================

def determine_approval_policy(request: AccessRequest) -> ApprovalPolicy:
    """
    Función que evalúa el contexto de la solicitud (AccessRequest)
    y retorna dinámicamente la estrategia de aprobación correcta.
    """
    
    # Prioridad 1: Bases de datos productivas (Máxima criticidad)
    if request.system_type == SystemType.PRODUCTIVE_DATABASE:
        return ProductiveDatabasePolicy()
    
    # Prioridad 2: Nivel de acceso ADMIN
    if request.access_level == AccessLevel.ADMIN:
        return AdminApprovalPolicy()
        
    # Prioridad 3: Accesos estándar (READ o WRITE en sistemas no críticos)
    return StandardApprovalPolicy()
