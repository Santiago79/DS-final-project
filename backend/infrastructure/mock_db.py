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