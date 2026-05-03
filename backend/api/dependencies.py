from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from domain.entities import User
from infrastructure.auth_provider import AuthProvider
from infrastructure.database import SessionLocal
from infrastructure.postgres import (
    PostgresUserRepository,
    PostgresAccessRequestRepository,
    PostgresNotificationRepository,
    PostgresAuditLogRepository,
)
from infrastructure.event_bus_impl import InMemoryEventBus
from infrastructure.observers import NotificationObserver, AuditLogObserver
from application.use_cases import AccessRequestUseCases

# ---------- Instancias únicas (se inicializan en setup_dependencies) ----------
user_repo_instance: PostgresUserRepository = None
request_repo_instance: PostgresAccessRequestRepository = None
event_bus_instance: InMemoryEventBus = InMemoryEventBus()

# ---------- Configuración de OAuth2 ----------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ---------- Funciones de dependencia ----------
def get_user_repository() -> PostgresUserRepository:
    return user_repo_instance

def get_request_repository() -> PostgresAccessRequestRepository:
    return request_repo_instance

def get_event_bus() -> InMemoryEventBus:
    return event_bus_instance

def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: PostgresUserRepository = Depends(get_user_repository)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales o el token ha expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = AuthProvider.decode_token(token)
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = user_repo.get_by_email(email)
    if user is None:
        raise credentials_exception
    return user

def get_access_request_use_cases(
    repo: PostgresAccessRequestRepository = Depends(get_request_repository),
    bus: InMemoryEventBus = Depends(get_event_bus)
) -> AccessRequestUseCases:
    return AccessRequestUseCases(repo, bus)

# ---------- Inicialización de dependencias reales ----------
def setup_dependencies():
    """Inicializa repositorios reales y suscribe observers al EventBus."""
    global user_repo_instance, request_repo_instance

    db = SessionLocal()

    # Repositorios reales
    user_repo_instance = PostgresUserRepository(db)
    request_repo_instance = PostgresAccessRequestRepository(db)

    # Observers
    notification_repo = PostgresNotificationRepository(db)
    audit_repo = PostgresAuditLogRepository(db)

    notif_observer = NotificationObserver(notification_repo, user_repo_instance, db)
    audit_observer = AuditLogObserver(audit_repo)

    # Suscribir al EventBus
    event_bus_instance.subscribe(notif_observer)
    event_bus_instance.subscribe(audit_observer)