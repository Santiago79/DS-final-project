from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from domain.entities import User

# Configuración (En un entorno real, esto iría en variables de entorno o un .env)
SECRET_KEY = "usfq_accessflow_super_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# Configuración de bcrypt para los hashes de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthProvider:
    """Proveedor de autenticación e identidad."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica que la contraseña en texto plano coincida con el hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Genera un hash bcrypt a partir de una contraseña plana."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
        """Genera un token JWT firmado con los datos básicos del usuario."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            
        # El payload incluye el rol para poder hacer validaciones en los endpoints (Issue #90)
        to_encode = {
            "sub": user.email,
            "role": user.role.value,
            "user_id": user.id,
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt