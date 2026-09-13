import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VisitorStatus(str, enum.Enum):
    REGISTERED = "registered"
    VERIFIED = "verified"


class Visitor(Base):
    """Visitante registrado. Nunca se elimina fisicamente."""

    __tablename__ = "visitors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cedula: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    status: Mapped[VisitorStatus] = mapped_column(Enum(VisitorStatus), default=VisitorStatus.REGISTERED)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
