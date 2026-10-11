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

    def _as_dict(self, form_data) -> dict:
        if hasattr(form_data, "model_dump"):
            return form_data.model_dump()
        if hasattr(form_data, "dict"):
            return form_data.dict()
        return dict(form_data)

    def create(self, user_data):
        """Create a new user. Raises 400 if the email is already registered."""
        data = self._as_dict(user_data)
        existing = self.db.get_by_email(data.get("email", ""))
        if existing:
            raise HTTPException(
                status_code=400, detail="El correo ya está registrado"
            )
        return self.db.create(data)

    def authenticate(self, form_data) -> Optional[object]:
        data = self._as_dict(form_data)
        email = data.get("email", "")
        password = data.get("password", "")
        if not email or not password:
            return None
        user = self.db.get_by_email(email)
        if not user:
            return None
        if not self.pwd.verify(password, user.password_hash):
            return None
        if not getattr(user, "is_active", True):
            return None
        return user

    def create_access_token(self, subject: str = None, sub: str = None) -> str:
        import time
        subject = subject or sub
        if not subject:
            raise ValueError("subject (sub) is required")
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


def get_auth_service(db: Session) -> AuthService:
    from app.repositories.user_repository import UserRepository
    return AuthService(UserRepository(db))
