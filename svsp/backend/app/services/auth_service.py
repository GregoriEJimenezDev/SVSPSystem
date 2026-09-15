from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    """Autenticacion: valida credenciales y emite tokens JWT."""

    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def login(self, email: str, password: str) -> str:
        user = self.repo.get_by_email(email)
        if not user or not user.is_active or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Credenciales invalidas o usuario inhabilitado")

        token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value, "modules": user.modules}
        )
        return token
