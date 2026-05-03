from domain.enums import UserRole
from domain.entities import User
from infrastructure.auth_provider import AuthProvider

MOCK_USERS_DB = []

class MockUserRepository:
    """Repositorio temporal para no ensuciar la API."""
    def get_by_email(self, email: str) -> User | None:
        return next((u for u in MOCK_USERS_DB if u.email == email), None)
        
    def save(self, user: User):
        global MOCK_USERS_DB
        # Eliminamos si ya existe para reemplazarlo (simulando un UPSERT)
        MOCK_USERS_DB = [u for u in MOCK_USERS_DB if u.email != user.email]
        MOCK_USERS_DB.append(user)


class MockRequestRepository:
    def __init__(self):
        self.requests = []

    def save(self, request):
        self.requests = [r for r in self.requests if r.id != request.id]
        self.requests.append(request)

    def get_by_id(self, request_id: str):
        return next((r for r in self.requests if str(r.id) == request_id), None)

    def get_all(self):
        return self.requests

class MockEventBus:
    def publish(self, event):
        print(f"[EventBus Mock] Evento publicado: {event.__class__.__name__}")