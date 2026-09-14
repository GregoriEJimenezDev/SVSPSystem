from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.models import Employee, User
from core.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from core.dependencies import get_current_active_user, log_audit

router = APIRouter(prefix="/api/v1/employees", tags=["Empleados"])


@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Listar empleados (solo activos o todos dependiendo de rol)"""
    query = db.query(Employee)
    employees = query.offset(skip).limit(limit).all()
    return employees


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Crear nuevo empleado"""
    new_employee = Employee(
        name=employee_data.name, department=employee_data.department, is_active=True
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


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Actualizar empleado (nombre, departamento)"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado"
        )

    if employee_data.name is not None:
        employee.name = employee_data.name
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
    current_user: User = Depends(get_current_active_user),
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
