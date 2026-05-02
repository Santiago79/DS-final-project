# application/request_service.py

from backend.domain.entities import User
from domain.enums import RequestStatus
from domain.exceptions import InvalidStateTransitionError, SelfApprovalError, UnauthorizedError

class RequestService:
    def __init__(self, request_repository):
        self.repository = request_repository
    
    def approve_request(self, request_id: str, reviewer: User) -> dict:
        """
        Aprueba una solicitud en el paso actual (Manager o Security).
        Si después de la aprobación la solicitud queda en APPROVED,
        la finaliza automáticamente pasándola a READY_FOR_PROVISIONING.
        """
        request = self.repository.get_by_id(request_id)
        if not request:
            return {"success": False, "error": "Solicitud no encontrada"}
        
        # 1. Delegar la aprobación al estado actual
        try:
            request.approve(reviewer)
        except (InvalidStateTransitionError, UnauthorizedError, SelfApprovalError) as e:
            return {"success": False, "error": str(e)}
        
        # 2.  COORDINACIÓN: si quedó en APPROVED, finalizarla
        if request.status == RequestStatus.APPROVED:
            request.finalize_approval()  # Esto pasa a READY_FOR_PROVISIONING
        
        # 3. Guardar los cambios
        self.repository.save(request)
        
        return {
            "success": True,
            "request_id": request.id,
            "new_status": request.status.value,
            "message": "Solicitud aprobada y lista para provisionar."
        }