from fastapi import APIRouter, Depends, HTTPException, status

from application.dtos import LoginRequest, TokenResponse
from infrastructure.auth_provider import AuthProvider
from api.dependencies import get_user_repository

router = APIRouter(tags=["Authentication"])

@router.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, user_repo = Depends(get_user_repository)):
    """Autentica a un usuario validando su email y contraseña."""
    
    # Delegamos la búsqueda al repositorio inyectado
    user = user_repo.get_by_email(request.email)
    
    if not user or not AuthProvider.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # El endpoint arma el payload según el feedback
    access_token = AuthProvider.create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "user_id": str(user.id)
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value
    )