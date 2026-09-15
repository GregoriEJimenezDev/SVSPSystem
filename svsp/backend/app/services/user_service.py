import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class EmailAlreadyExistsError(Exception):
    pass


class UserService:
    """Reglas de negocio de usuarios. Solo un AdminPRO puede invocar estos
    metodos (verificado en la capa de routers via dependencias de RBAC).
    """

    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def create_user(self, data: UserCreate) -> User:
        if self.repo.get_by_email(data.email):
            raise EmailAlreadyExistsError("Ya existe un usuario con ese correo")

        user = User(
            full_name=data.full_name,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
            modules=data.modules,
        )
        return self.repo.add(user)

    def list_users(self) -> list[User]:
        return self.repo.list()

    def update_user(self, user_id: uuid.UUID, data: UserUpdate) -> User | None:
        user = self.repo.get(user_id)
        if not user:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        return self.repo.save(user)
