import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_module
from app.models.employee import EmployeeStatus
from app.schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate
from app.services.employee_service import EmployeeService

router = APIRouter(
    prefix="/api/employees",
    tags=["Empleados"],
    dependencies=[Depends(require_module("asistencia"))],
)


@router.get("/", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db)):
    return EmployeeService(db).list()


@router.post("/", response_model=EmployeeOut)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    return EmployeeService(db).create(payload)


@router.put("/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: uuid.UUID, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    return EmployeeService(db).update(employee_id, payload)


@router.post("/{employee_id}/disable", response_model=EmployeeOut)
def disable_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return EmployeeService(db).set_status(employee_id, EmployeeStatus.DISABLED)


@router.post("/{employee_id}/enable", response_model=EmployeeOut)
def enable_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return EmployeeService(db).set_status(employee_id, EmployeeStatus.ACTIVE)
