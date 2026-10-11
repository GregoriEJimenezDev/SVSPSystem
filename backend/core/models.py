from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Time,
    ForeignKey,
    Text,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship, Mapped
import enum

from core.database import Base


class ModuleEnum(str, enum.Enum):
    ASISTENCIA = "asistencia"
    VISITAS = "visitas"
    ADMINPRO = "adminpro"


class RoleEnum(str, enum.Enum):
    ADMINPRO = "AdminPRO"
    ASISTENCIA = "Asistencia"
    VISITAS = "Visitas"


class Department(Base):
    """Departamentos administrables (filtro de empleados y reportes)."""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    modules = Column(JSON, default=list)  # ["asistencia", "visitas"]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="employee"
    )
    justifications: Mapped[List["Justification"]] = relationship(
        "Justification", back_populates="employee"
    )


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    date = Column(Date, nullable=False, index=True)
    check_in = Column(Time, nullable=True)
    check_out = Column(Time, nullable=True)
    total_hours = Column(String(20), nullable=True)
    source = Column(String(50), default="biometric")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="attendances"
    )
    justification_id = Column(Integer, ForeignKey("justifications.id"), nullable=True)
    justification: Mapped[Optional["Justification"]] = relationship(
        "Justification", back_populates="attendances"
    )


class Justification(Base):
    __tablename__ = "justifications"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="justifications"
    )
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="justification"
    )


class Visitor(Base):
    __tablename__ = "visitors"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    document_number = Column(String(50), nullable=False, index=True)
    visited_person = Column(String(255), nullable=True)  # ¿A quién visita?
    institution = Column(String(255), nullable=True)  # ¿De qué institución viene?
    visit_justification = Column(Text, nullable=True)  # Justificación de la visita
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
