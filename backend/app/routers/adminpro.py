from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.models import User, Employee, Attendance, Justification, Visitor, AuditLog
from core.schemas import UserCreate, UserUpdate, UserResponse, AuditLogResponse
from core.dependencies import get_current_active_user, require_adminpro, log_audit
from datetime import datetime


router = APIRouter(prefix="/api/v1/adminpro", tags=["AdminPRO"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_adminpro),
):
    """Crear nuevo usuario del sistema (solo AdminPRO)"""
    # Verificar si el usuario ya existe
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado",
        )

    # Hashear contraseña
    hashed_pw = (
        user_data.hashed_password
    )  # Ya viene hasheado desde el frontend o usar hash_password
    if not hashed_pw.startswith("$2"):
        hashed_pw = hash_password(user_data.password)

    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
        modules=user_data.modules or [],
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="create_user",
        entity_type="user",
        entity_id=new_user.id,
        details={
            "email": new_user.email,
            "modules": new_user.modules,
            "created_by": current_user.email,
        },
        request=request,
    )

    return new_user


@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_adminpro),
):
    """Listar todos los usuarios del sistema"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_adminpro),
):
    """Actualizar usuario (rol, módulos, estado)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.modules is not None:
        user.modules = user_data.modules
    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="update_user",
        entity_type="user",
        entity_id=user.id,
        details={
            "email": user.email,
            "modules": user.modules,
            "is_active": user.is_active,
        },
        request=request,
    )

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_adminpro),
):
    """Inhabilitar usuario (soft delete)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    # No permitir inhabilitar al último AdminPRO
    adminpro_count = db.query(User).filter(User.modules.contains(["adminpro"])).count()

    if user.is_active and adminpro_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede inhabilitar al último administrador",
        )

    user.is_active = False
    db.commit()

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="disable_user",
        entity_type="user",
        entity_id=user.id,
        details={"email": user.email, "was_active": user.is_active},
        request=request,
    )


@router.get("/audit-log", response_model=List[AuditLogResponse])
def get_audit_log(
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_adminpro),
):
    """Obtener bitácora de auditoría"""
    query = db.query(AuditLog)

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/statistics")
def get_system_statistics(
    db: Session = Depends(get_db), current_user: User = Depends(require_adminpro)
):
    """Estadísticas generales del sistema"""
    from sqlalchemy import func

    total_employees = db.query(Employee).count()
    active_employees = db.query(Employee).filter(Employee.is_active == True).count()
    inactive_employees = db.query(Employee).filter(Employee.is_active == False).count()
    total_users = db.query(User).count()
    total_visitors = db.query(Visitor).count()
    total_audit_logs = db.query(AuditLog).count()

    from core.models import Attendance
    from datetime import date

    today = date.today()
    today_attendance = db.query(Attendance).filter(Attendance.date == today).count()

    return {
        "empleados": {
            "total": total_employees,
            "activos": active_employees,
            "inactivos": inactive_employees,
        },
        "usuarios": {"total": total_users},
        "visitantes": {"total_registrados": total_visitors},
        "auditoria": {"total_registros": total_audit_logs},
        "asistencia_hoy": today_attendance,
    }
