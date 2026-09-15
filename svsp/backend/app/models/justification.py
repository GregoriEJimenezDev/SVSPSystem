import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JustificationType(str, enum.Enum):
    PERMISO = "permiso"
    LICENCIA_MEDICA = "licencia_medica"
    VACACIONES = "vacaciones"
    OTRO = "otro"


class Justification(Base):
    """Justificacion de ausencia que puede cubrir un rango de fechas."""

    __tablename__ = "justifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    type: Mapped[JustificationType] = mapped_column(Enum(JustificationType), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str] = mapped_column(String(500), nullable=True)

    employee = relationship("Employee", back_populates="justifications")
