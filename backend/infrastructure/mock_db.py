from domain.enums import UserRole
from domain.entities import User
from infrastructure.auth_provider import AuthProvider

MOCK_USERS_DB = [
    User(
        name="System Admin", 
        email="admin@accessflow.com", 
        hashed_password=AuthProvider.get_password_hash("admin123"), 
        role=UserRole.SYSTEM_ADMIN
    ),
    User(
        name="Employee", 
        email="employee@accessflow.com", 
        hashed_password=AuthProvider.get_password_hash("employee123"), 
        role=UserRole.EMPLOYEE
    ),
    User(
        name="Manager", 
        email="manager@accessflow.com", 
        hashed_password=AuthProvider.get_password_hash("manager123"), 
        role=UserRole.MANAGER
    ),
    User(
        name="Security Reviewer", 
        email="security@accessflow.com", 
        hashed_password=AuthProvider.get_password_hash("security123"), 
        role=UserRole.SECURITY_REVIEWER
    ),
    User(
        name="IT Admin", 
        email="itadmin@accessflow.com", 
        hashed_password=AuthProvider.get_password_hash("itadmin123"), 
        role=UserRole.IT_ADMIN
    ),
]

class MockUserRepository:
    """Repositorio temporal para no ensuciar la API."""
    def get_by_email(self, email: str) -> User | None:
        return next((u for u in MOCK_USERS_DB if u.email == email), None)

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