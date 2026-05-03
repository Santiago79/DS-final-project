from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.endpoints import router as api_router
from domain.enums import UserRole
from domain.entities import User
from infrastructure.auth_provider import AuthProvider
from api.dependencies import get_user_repository

def seed_test_users():
    """Verifica y crea los usuarios de prueba en la base de datos si no existen."""
    user_repo = get_user_repository()
    
    users_to_seed = [
        {"name": "System Admin", "email": "admin@accessflow.com", "password": "admin123", "role": UserRole.SYSTEM_ADMIN},
        {"name": "Employee", "email": "employee@accessflow.com", "password": "employee123", "role": UserRole.EMPLOYEE},
        {"name": "Manager", "email": "manager@accessflow.com", "password": "manager123", "role": UserRole.MANAGER},
        {"name": "Security Reviewer", "email": "security@accessflow.com", "password": "security123", "role": UserRole.SECURITY_REVIEWER},
        {"name": "IT Admin", "email": "itadmin@accessflow.com", "password": "itadmin123", "role": UserRole.IT_ADMIN},
    ]
    
    for u_data in users_to_seed:
        if not user_repo.get_by_email(u_data["email"]):
            hashed_pw = AuthProvider.get_password_hash(u_data["password"])
            
            new_user = User(
                name=u_data["name"],
                email=u_data["email"],
                hashed_password=hashed_pw,
                role=u_data["role"]
            )
            
            # Cambiado a "add" para coincidir con la nueva interfaz
            user_repo.add(new_user)
            print(f"✅ Usuario semilla creado: {u_data['email']} [{u_data['role'].value}]")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Event ---
    print("Iniciando AccessFlow API...")
    
    # Intenta crear las tablas si el archivo de DB ya existe
    try:
        from infrastructure.database import create_all_tables
        create_all_tables()
        print("Tablas de base de datos validadas/creadas.")
    except ImportError:
        pass # Ignorar si Persona 3 aún no ha subido el archivo database.py
        
    seed_test_users()
    yield
    # --- Shutdown Event ---
    print("Apagando AccessFlow API...")


app = FastAPI(
    title="AccessFlow API",
    description="API para la gestión y aprobación de accesos en USFQ",
    version="1.0.0",
    lifespan=lifespan
)

# Registrar las rutas
app.include_router(api_router)