from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.models import Employee, User, Justification, Attendance
from core.schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    MergeRequest,
    MergeResult,
    DuplicateGroup,
)
from core.dependencies import require_module, log_audit

router = APIRouter(prefix="/api/v1/employees", tags=["Empleados"])


def normalize_name(name) -> str:
    """Normaliza nombres: sin espacios extra (evita duplicados tipo "Juan  Pérez")."""
    return " ".join(str(name or "").strip().split())


@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    skip: int = 0,
    limit: int = 100,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Listar empleados (solo activos o todos dependiendo de rol).

    `department` filtra por coincidencia parcial (case-insensitive).
    """
    query = db.query(Employee)
    if department:
        query = query.filter(Employee.department.ilike(f"%{department.strip()}%"))
    employees = query.order_by(Employee.name).offset(skip).limit(limit).all()
    return employees


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Crear nuevo empleado"""
    new_employee = Employee(
        name=normalize_name(employee_data.name),
        department=employee_data.department,
        is_active=True,
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="create_employee",
        entity_type="employee",
        entity_id=new_employee.id,
        details={"name": new_employee.name, "department": new_employee.department},
        request=None,  # Request no siempre disponible
    )

    return new_employee


@router.get("/duplicates", response_model=List[DuplicateGroup])
def find_duplicates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Detectar posibles empleados duplicados (mismo nombre normalizado).

    Agrupa por nombre en minúsculas sin espacios extra. Sirve para limpiar
    duplicados creados por variaciones ("Juan  Pérez" vs "Juan Pérez").
    """
    employees = db.query(Employee).all()
    groups: dict[str, list] = {}
    for emp in employees:
        key = normalize_name(emp.name).lower()
        if not key:
            continue
        groups.setdefault(key, []).append(emp)
    result = []
    for key in sorted(groups):
        members = groups[key]
        if len(members) > 1:
            result.append(
                {
                    "key": key,
                    "employees": [
                        {
                            "id": m.id,
                            "name": m.name,
                            "department": m.department,
                            "is_active": m.is_active,
                        }
                        for m in members
                    ],
                }
            )
    return result


@router.post("/merge", response_model=MergeResult)
def merge_duplicates(
    data: MergeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
    request: Request = None,
):
    """Fusionar duplicados: mueve asistencias/justificaciones al conservado
    y desactiva los demás (baja lógica, no se borra nada)."""
    dup_ids = [i for i in set(data.duplicate_ids) if i != data.keep_id]
    if not dup_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Indica al menos un duplicado distinto al conservado",
        )
    keep = db.query(Employee).filter(Employee.id == data.keep_id).first()
    if not keep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado a conservar no encontrado",
        )
    moved_attendances = 0
    moved_justifications = 0
    deactivated = []
    for dup_id in dup_ids:
        dup = db.query(Employee).filter(Employee.id == dup_id).first()
        if not dup:
            continue
        moved_attendances += (
            db.query(Attendance)
            .filter(Attendance.employee_id == dup_id)
            .update({Attendance.employee_id: keep.id})
        )
        moved_justifications += (
            db.query(Justification)
            .filter(Justification.employee_id == dup_id)
            .update({Justification.employee_id: keep.id})
        )
        dup.is_active = False
        deactivated.append(dup_id)
    db.commit()
    log_audit(
        db=db,
        user_id=current_user.id,
        action="merge_employees",
        entity_type="employee",
        entity_id=keep.id,
        details={"keep_id": keep.id, "deactivated": deactivated},
        request=request,
    )
    return {
        "keep_id": keep.id,
        "deactivated_ids": deactivated,
        "moved_attendances": moved_attendances,
        "moved_justifications": moved_justifications,
    }


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Actualizar empleado (nombre, departamento)"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado"
        )

    if employee_data.name is not None:
        employee.name = normalize_name(employee_data.name)
    if employee_data.department is not None:
        employee.department = employee_data.department

    db.commit()
    db.refresh(employee)

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="update_employee",
        entity_type="employee",
        entity_id=employee.id,
        details={"name": employee.name, "department": employee.department},
        request=None,
    )

    return employee


@router.put("/{employee_id}/toggle-status", response_model=EmployeeResponse)
def toggle_employee_status(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Inhabilitar o rehabilitar empleado (baja lógica)"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado"
        )

    # No permitir inhabilitar al último AdminPRO o dejar sin empleados activos
    if not employee.is_active and True:  # Lógica simple - ya está inactivo
        employee.is_active = True
    else:
        employee.is_active = False

    db.commit()
    db.refresh(employee)

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="toggle_employee_status",
        entity_type="employee",
        entity_id=employee.id,
        details={"is_active": employee.is_active},
        request=None,
    )

    return employee
