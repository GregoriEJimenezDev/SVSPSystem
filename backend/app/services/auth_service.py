from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db_repo):
        self.db = db_repo
        self.pwd = pwd_context

    def authenticate(self, form_data: dict) -> Optional[dict]:
        user = self.db.query(type('User', (), {'email': form_data.get('email', '')})).first()
        # Simplified - in real usage would query properly
        if not user:
            return None
        if not self.pwd.verify(form_data.get('password', ''), user.password_hash):
            return None
        if not getattr(user, 'is_active', True):
            return None
        return user

    def create_access_token(self, subject: str) -> str:
        import time
        issued_at = time.time()
        expires = issued_at + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        token = jwt.encode(
            {"sub": subject, "iat": issued_at, "exp": expires},
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return token

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                return None
            return {"email": email}
        except JWTError:
            return None


def get_auth_service(db) -> AuthService:
    from app.dependencies import get_db
    from app.repositories.user_repository import UserRepository
    return AuthService(get_db())