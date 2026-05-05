from domain.enums import RequestStatus
from fastapi import HTTPException
from domain.entities import User
from domain.factories import AccessRequestFactory
from domain.commands import (
    CreateRequestCommand, ApproveRequestCommand, RejectRequestCommand, 
    ProvisionAccessCommand, RequestChangesCommand, SubmitRequestCommand,
    CancelRequestCommand
)
from application.dtos import CreateAccessRequestDTO

class AccessRequestUseCases:
    def __init__(self, request_repo, event_bus):
        self.repo = request_repo
        self.event_bus = event_bus

    def create_request(self, dto: CreateAccessRequestDTO, user: User):
        request = AccessRequestFactory.create(
            requester_id=user.id,
            requester_name=user.name,
            target_system=dto.target_system,
            access_level=dto.access_level,
            justification=dto.justification,
            system_type=dto.system_type,
            expiration_date=dto.expiration_date,
            manager_id=None
        )
        
        # 1. Insertar primero
        self.repo.add(request)
        
        # 2. Ejecutar comandos y cambiar estado
        CreateRequestCommand(request, self.event_bus).execute()
        SubmitRequestCommand(request, self.event_bus).execute()
        
        # 3. Actualizar la BD con los cambios
        self.repo.update(request)
        return request

    def get_request(self, request_id: str):
        request = self.repo.get_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        return request

    def list_requests(self, user: User):
        return self.repo.get_all()

    def approve_request(self, request_id: str, reviewer: User):
        request = self.get_request(request_id)
        ApproveRequestCommand(request, self.event_bus, reviewer).execute()
        
        from domain.enums import RequestStatus
        if request.status == RequestStatus.APPROVED:
            request.finalize_approval()
            
        self.repo.update(request)
        return request

    def reject_request(self, request_id: str, reviewer: User, reason: str):
        request = self.get_request(request_id)
        RejectRequestCommand(request, self.event_bus, reviewer, reason).execute()
        self.repo.update(request)
        return request

    def request_changes(self, request_id: str, reviewer: User, comment: str):
        request = self.get_request(request_id)
        RequestChangesCommand(request, self.event_bus, reviewer, comment).execute()
        self.repo.update(request)
        return request

    def provision_request(self, request_id: str, admin: User):
        request = self.get_request(request_id)
        ProvisionAccessCommand(request, self.event_bus, admin).execute()
        self.repo.update(request)
        return request

    def cancel_request(self, request_id: str, user: User):
        request = self.get_request(request_id)
        CancelRequestCommand(request, self.event_bus).execute()
        self.repo.update(request)
        return request
    def return_to_draft(self, request_id: str, user: User):
        request = self.get_request(request_id)
        # Validar que el usuario sea el dueño
        if request.requester_id != user.id:
            raise HTTPException(status_code=403, detail="Solo el solicitante puede editar esta solicitud.")
        request.return_to_draft()  # Llama al método del estado
        self.repo.update(request)
        return request
    def update_request(self, request_id: str, dto: CreateAccessRequestDTO, user: User):
        request = self.get_request(request_id)
        if request.requester_id != user.id:
            raise HTTPException(status_code=403, detail="Solo el solicitante puede editar esta solicitud.")
        if request.status not in [RequestStatus.DRAFT, RequestStatus.CHANGES_REQUESTED]:
            raise HTTPException(status_code=400, detail="La solicitud solo puede editarse en estado DRAFT o cuando se solicitaron cambios.")

        # Si está en CHANGES_REQUESTED, primero la movemos a DRAFT
        if request.status == RequestStatus.CHANGES_REQUESTED:
            request.return_to_draft()  # Este método ya existe en el estado

        # Actualizar campos
        request.target_system = dto.target_system
        request.access_level = dto.access_level
        request.justification = dto.justification
        request.system_type = dto.system_type
        request.expiration_date = dto.expiration_date
        # manager_id se mantiene igual

        self.repo.update(request)
        return request
    def submit_request(self, request_id: str, user: User):
        request = self.get_request(request_id)
        if request.requester_id != user.id:
            raise HTTPException(status_code=403, detail="Solo el solicitante puede enviar esta solicitud.")
        if request.status != RequestStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Solo se puede enviar una solicitud en estado DRAFT.")

        SubmitRequestCommand(request, self.event_bus).execute()
        self.repo.update(request)
        return request