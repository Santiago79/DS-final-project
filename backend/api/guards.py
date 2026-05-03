from typing import List
from fastapi import Depends, HTTPException, status

from domain.entities import User
from domain.enums import UserRole
from api.dependencies import get_current_user

def require_role(required_role: UserRole):
    """
    Guard que exige un rol específico para acceder al endpoint.
    SYSTEM_ADMIN siempre tiene acceso total.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == UserRole.SYSTEM_ADMIN:
            return current_user
            
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Acceso denegado. Se requiere el rol: {required_role.name}"
            )
        return current_user
        
    return role_checker


def require_any_role(required_roles: List[UserRole]):
    """
    Guard que exige al menos uno de los roles de la lista para acceder.
    SYSTEM_ADMIN siempre tiene acceso total.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == UserRole.SYSTEM_ADMIN:
            return current_user
            
        if current_user.role not in required_roles:
            roles_str = ", ".join([r.name for r in required_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Acceso denegado. Se requiere alguno de estos roles: {roles_str}"
            )
        return current_user
        
    return role_checker