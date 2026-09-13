import enum
import uuid

from sqlalchemy import JSON, Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, enum.Enum):
    ADMINPRO = "adminpro"
    STANDARD = "standard"


class Module(str, enum.Enum):
    ASISTENCIA = "asistencia"
    VISITAS = "visitas"


class User(Base):
    """Usuario del sistema. Los usuarios 'standard' solo acceden a los
    modulos listados en `modules`. Un AdminPRO tiene acceso total sin
    necesidad de revisar `modules`.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STANDARD, nullable=False)
    modules: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
