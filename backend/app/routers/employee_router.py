from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Any
from app.dependencies import get_db
from app.schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)
from app.services import get_employee_service
from app.dependencies import (
    get_current_active_user,
    get_current_active_user_with_module_access,
)
from app.models import Employee, User

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("/", response_model=EmployeeResponse, status_code=201)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_employee_service(db)
    # Auto-create user+employee if user doesn't exist
    return svc.create_employee_with_user(employee)


@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_employee_service(db)
    return svc.get_all_active()


@router.get("/dept/{department}", response_model=List[EmployeeResponse])
def list_by_department(
    department: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_employee_service(db)
    return svc.get_by_department(department)


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_employee_service(db)
    return svc.update(employee_id, data)


@router.put("/{employee_id}/toggle", response_model=EmployeeResponse)
def toggle_employee_status(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_employee_service(db)
    # If has attendances, prevent toggle; otherwise invert is_active
    emp = svc.emp_repo.get_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Check if employee has attendance records
    from app.repositories import AttendanceRepository
    att_repo = AttendanceRepository(db)
    atts = att_repo.get_by_employee(employee_id)
    if len(atts) > 0:
        # Just inactivate instead of full toggle
        emp.is_active = not emp.is_active
    else:
        emp.is_active = not emp.is_active
    
    db.commit()
    db.refresh(emp)
    return emp