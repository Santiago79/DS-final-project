from domain.enums import UserRole
from domain.entities import User
from infrastructure.auth_provider import AuthProvider

MOCK_USERS_DB = [
    User(
        name="Admin Prueba", 
        email="admin@usfq.edu.ec", 
        hashed_password=AuthProvider.get_password_hash("admin123"), 
        role=UserRole.SYSTEM_ADMIN
    ),
    User(
        name="Empleado Prueba", 
        email="empleado@usfq.edu.ec", 
        hashed_password=AuthProvider.get_password_hash("emp123"), 
        role=UserRole.EMPLOYEE
    )
]

class MockUserRepository:
    """Repositorio temporal para no ensuciar la API."""
    def get_by_email(self, email: str) -> User | None:
        return next((u for u in MOCK_USERS_DB if u.email == email), None)


class MockRequestRepository:
    def __init__(self):
        self.requests = []

    def save(self, request):
        # Actualiza o inserta
        self.requests = [r for r in self.requests if r.id != request.id]
        self.requests.append(request)

    def get_by_id(self, request_id: str):
        return next((r for r in self.requests if str(r.id) == request_id), None)

    def get_all(self):
        return self.requests

class MockEventBus:
    def publish(self, event):
        # En consola para ver qué eventos se están disparando
        print(f"[EventBus Mock] Evento publicado: {event.__class__.__name__}")