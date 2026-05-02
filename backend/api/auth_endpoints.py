from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from domain.enums import UserRole
from domain.entities import User
from infrastructure.auth_provider import AuthProvider

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ============================================================
# DTOs (Data Transfer Objects)
# ============================================================

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

# ============================================================
# MOCK BASE DE DATOS (Se reemplazará en el Issue #87)
# ============================================================

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

def get_user_by_email(email: str) -> User | None:
    return next((u for u in MOCK_USERS_DB if u.email == email), None)

# ============================================================
# Endpoints
# ============================================================

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """
    Autentica a un usuario validando su email y contraseña.
    Retorna un JWT si las credenciales son válidas.
    """
    # 1. Buscar usuario
    user = get_user_by_email(request.email)
    
    # 2. Validar existencia y contraseña
    if not user or not AuthProvider.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Generar token
    access_token = AuthProvider.create_access_token(user)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value
    )