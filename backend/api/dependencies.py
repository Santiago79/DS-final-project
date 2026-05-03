from infrastructure.mock_db import MockUserRepository

def get_user_repository():
    """Inyecta el repositorio. En el futuro se cambiará por PostgresUserRepository."""
    return MockUserRepository()