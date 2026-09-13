import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Decodifica el JWT y carga el usuario autenticado. Se usa como
    dependencia en cada endpoint protegido.
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido o expirado")

    user_id = payload.get("sub")
    user = UserRepository(db).get(uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario invalido o inhabilitado")

    return user


def require_module(module: str):
    """Fabrica de dependencias de RBAC: exige que el usuario sea AdminPRO
    o tenga el modulo indicado dentro de sus privilegios asignados.
    Se aplica en el backend, no solo en el frontend.
    """

    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == UserRole.ADMINPRO:
            return current_user
        if module not in (current_user.modules or []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes acceso al modulo '{module}'",
            )
        return current_user

    return _check


def require_adminpro(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMINPRO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol AdminPRO")
    return current_user
