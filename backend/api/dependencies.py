from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from domain.entities import User
from infrastructure.auth_provider import AuthProvider
from infrastructure.mock_db import MockUserRepository

from infrastructure.mock_db import MockRequestRepository, MockEventBus
from application.use_cases import AccessRequestUseCases

# Instancias en memoria para que sobrevivan a las peticiones
request_repo_instance = MockRequestRepository()
event_bus_instance = MockEventBus()

# Le indica a FastAPI y a Swagger/OpenAPI dónde está el endpoint para pedir el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_user_repository():
    """Inyecta el repositorio. En el futuro se cambiará por PostgresUserRepository."""
    return MockUserRepository()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: MockUserRepository = Depends(get_user_repository)
) -> User:
    """
    Extrae el token JWT de la cabecera, lo decodifica y busca al usuario
    correspondiente en el repositorio inyectado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales o el token ha expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. Decodificamos el token usando tu AuthProvider
        payload = AuthProvider.decode_token(token)
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # 2. Buscamos al usuario en la base de datos (mock por ahora)
    user = user_repo.get_by_email(email)
    
    # 3. Si el usuario ya no existe (ej. fue eliminado), bloqueamos el acceso
    if user is None:
        raise credentials_exception
        
    return user


def get_request_repository():
    return request_repo_instance

def get_event_bus():
    return event_bus_instance

def get_access_request_use_cases(
    repo = Depends(get_request_repository),
    bus = Depends(get_event_bus)
) -> AccessRequestUseCases:
    """Inyecta la capa de aplicación con sus dependencias resueltas."""
    return AccessRequestUseCases(repo, bus)