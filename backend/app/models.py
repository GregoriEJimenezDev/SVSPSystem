from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Junction table for role-permission many-to-many (expansion friendly)
roles_permissions = Table(
    "roles_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    roles = relationship(
        "Role", secondary=roles_permissions, back_populates="permissions"
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # para roles predefinidos
    permissions = relationship(
        "Permission", secondary=roles_permissions, back_populates="roles"
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    role = relationship("Role", lazy="select")
    employee = relationship("Employee", uselist=False, cascade="all, delete-orphan")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)  # lógico (habilitado/inhabilitado)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    attendances = relationship("Attendance", back_populates="employee")
    justifications = relationship("Justification", back_populates="employee")


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=True)
    total_hours = Column(String, nullable=True)  # stored as string "HH:MM" or minutes
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    justification_id = Column(Integer, ForeignKey("justifications.id"), nullable=True)

    employee = relationship("Employee", back_populates="attendances")
    justification = relationship("Justification", back_populates="attendance")


class Justification(Base):
    __tablename__ = "justifications"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    type = Column(String, nullable=False)  # 'permiso', 'licencia', 'vacaciones', etc.
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    employee = relationship("Employee", back_populates="justifications")
    attendance = relationship("Attendance", back_populates="justification", uselist=False)


class Visitor(Base):
    __tablename__ = "visitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    cedula = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # No physical delete: soft delete via is_active