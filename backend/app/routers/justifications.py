from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.models import Employee, Justification, User
from core.schemas import (
    JustificationCreate,
    JustificationUpdate,
    JustificationResponse,
    AttendanceStats,
)
from core.dependencies import require_module, log_audit
from datetime import date


router = APIRouter(prefix="/api/v1/justifications", tags=["Justificaciones"])


@router.post(
    "/", response_model=JustificationResponse, status_code=status.HTTP_201_CREATED
)
def create_justification(
    justification_data: JustificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Crear justificación por rango de fechas"""
    # Verificar que el empleado existe
    employee = (
        db.query(Employee).filter(Employee.id == justification_data.employee_id).first()
    )
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado"
        )

    # Verificar solapamiento con justificaciones existentes
    existing = (
        db.query(Justification)
        .filter(
            Justification.employee_id == justification_data.employee_id,
            Justification.is_active == True,
            # Solapamiento: la nueva justificación empieza antes de que termine la existente
            # y termina después de que empiece la existente
            (Justification.start_date <= justification_data.end_date)
            & (Justification.end_date >= justification_data.start_date),
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hay una justificación que solapa con estas fechas. "
            "Modifique el rango o anule la justificación existente.",
        )

    new_justification = Justification(
        employee_id=justification_data.employee_id,
        type=justification_data.type,
        description=justification_data.description,
        start_date=justification_data.start_date,
        end_date=justification_data.end_date,
        is_active=True,
    )

    db.add(new_justification)
    db.commit()
    db.refresh(new_justification)

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="create_justification",
        entity_type="justification",
        entity_id=new_justification.id,
        details={
            "employee_id": justification_data.employee_id,
            "type": justification_data.type,
            "start_date": str(justification_data.start_date),
            "end_date": str(justification_data.end_date),
        },
        request=None,
    )

    return new_justification


@router.get("/employee/{employee_id}", response_model=List[JustificationResponse])
def list_justifications(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Listar justificaciones de un empleado"""
    justifications = (
        db.query(Justification).filter(Justification.employee_id == employee_id).all()
    )
    return justifications


@router.put("/{justification_id}", response_model=JustificationResponse)
def update_justification(
    justification_id: int,
    justification_data: JustificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Actualizar justificación"""
    justification = (
        db.query(Justification).filter(Justification.id == justification_id).first()
    )
    if not justification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Justificación no encontrada"
        )

    if justification_data.type is not None:
        justification.type = justification_data.type
    if justification_data.description is not None:
        justification.description = justification_data.description
    if justification_data.start_date is not None:
        justification.start_date = justification_data.start_date
    if justification_data.end_date is not None:
        justification.end_date = justification_data.end_date
    if justification_data.is_active is not None:
        justification.is_active = justification_data.is_active

    db.commit()
    db.refresh(justification)

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="update_justification",
        entity_type="justification",
        entity_id=justification.id,
        details={
            "type": justification.type,
            "start_date": str(justification.start_date),
            "end_date": str(justification.end_date),
            "is_active": justification.is_active,
        },
        request=None,
    )

    return justification
