class AccessFlowError(Exception):
    """Excepción base para todos los errores de AccessFlow."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ValidationError(AccessFlowError):
    """Error cuando los datos de entrada no cumplen las reglas básicas."""
    pass


class DomainError(Exception):
    """Excepción base para errores del dominio."""
    pass


class InvalidStateTransitionError(DomainError):
    """Error cuando una transición de estado no es válida."""
    pass


class NotFoundError(DomainError):
    """Error cuando una entidad no existe en el repositorio."""
    pass


class UnauthorizedError(DomainError):
    """Error cuando un usuario no tiene permisos para una acción."""
    pass


class SelfApprovalError(DomainError):
    """Error cuando un solicitante intenta aprobar su propia solicitud."""
    pass


class RejectedRequestError(DomainError):
    """Error cuando se intenta modificar una solicitud ya rechazada."""
    pass


class ExpirationRequiredError(DomainError):
    """Error cuando una solicitud ADMIN no tiene fecha de expiración."""
    pass