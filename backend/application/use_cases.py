from fastapi import HTTPException
from domain.entities import User
from domain.factories import AccessRequestFactory
from domain.commands import (
    CreateRequestCommand, ApproveRequestCommand, RejectRequestCommand, 
    ProvisionAccessCommand, CancelRequestCommand, RequestChangesCommand, SubmitRequestCommand
)
from application.dtos import CreateAccessRequestDTO

class AccessRequestUseCases:
    def __init__(self, request_repo, event_bus):
        self.repo = request_repo
        self.event_bus = event_bus

    def create_request(self, dto: CreateAccessRequestDTO, user: User):
        # 1. Usar Factory para crear la entidad
        request = AccessRequestFactory.create(
            requester_id=user.id,
            requester_name=user.name,
            target_system=dto.target_system,
            access_level=dto.access_level,
            justification=dto.justification,
            system_type=dto.system_type,
            expiration_date=dto.expiration_date,
            manager_id=dto.manager_id
        )
        
        # 2. Ejecutar comandos de creación y envío
        CreateRequestCommand(request, self.event_bus).execute()
        SubmitRequestCommand(request, self.event_bus).execute()
        
        # 3. Guardar en BD
        self.repo.save(request)
        return request

    def get_request(self, request_id: str):
        request = self.repo.get_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        return request

    def approve_request(self, request_id: str, reviewer: User):
        request = self.get_request(request_id)
        ApproveRequestCommand(request, self.event_bus, reviewer).execute()
        self.repo.save(request)
        return request

    def reject_request(self, request_id: str, reviewer: User, reason: str):
        request = self.get_request(request_id)
        RejectRequestCommand(request, self.event_bus, reviewer, reason).execute()
        self.repo.save(request)
        return request

    def request_changes(self, request_id: str, reviewer: User, comment: str):
        request = self.get_request(request_id)
        RequestChangesCommand(request, self.event_bus, reviewer, comment).execute()
        self.repo.save(request)
        return request

    def provision_request(self, request_id: str, admin: User):
        request = self.get_request(request_id)
        ProvisionAccessCommand(request, self.event_bus, admin).execute()
        self.repo.save(request)
        return request