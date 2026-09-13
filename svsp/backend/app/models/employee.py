import enum
import uuid

from sqlalchemy import Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmployeeStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class Employee(Base):
    """Empleado. Nunca se elimina fisicamente: solo cambia su `status`."""

    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[EmployeeStatus] = mapped_column(
        Enum(EmployeeStatus), default=EmployeeStatus.ACTIVE, nullable=False
    )

    attendances = relationship("Attendance", back_populates="employee")
    justifications = relationship("Justification", back_populates="employee")
