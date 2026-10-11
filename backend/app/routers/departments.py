from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.models import Department, Employee, User
from core.schemas import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from core.dependencies import require_module, log_audit

router = APIRouter(prefix="/api/v1/departments", tags=["Departamentos"])


def _norm(name: str) -> str:
    return " ".join(name.strip().split())


@router.get("/", response_model=List[DepartmentResponse])
def list_departments(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Listar departamentos (por defecto solo activos)."""
    query = db.query(Department)
    if active_only:
        query = query.filter(Department.is_active == True)  # noqa: E712
    return query.order_by(Department.name).all()


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
    request: Request = None,
):
    """Crear un departamento."""
    name = _norm(data.name)
    existing = db.query(Department).filter(Department.name.ilike(name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El departamento ya existe",
        )
    dept = Department(name=name, is_active=True)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    log_audit(
        db=db,
        user_id=current_user.id,
        action="create_department",
        entity_type="department",
        entity_id=dept.id,
        details={"name": dept.name},
        request=request,
    )
    return dept


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
    request: Request = None,
):
    """Renombrar o (re)habilitar un departamento."""
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Departamento no encontrado"
        )
    if data.name is not None:
        name = _norm(data.name)
        dup = (
            db.query(Department)
            .filter(Department.name.ilike(name), Department.id != department_id)
            .first()
        )
        if dup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro departamento con ese nombre",
            )
        dept.name = name
    if data.is_active is not None:
        dept.is_active = data.is_active
    db.commit()
    db.refresh(dept)
    log_audit(
        db=db,
        user_id=current_user.id,
        action="update_department",
        entity_type="department",
        entity_id=dept.id,
        details={"name": dept.name, "is_active": dept.is_active},
        request=request,
    )
    return dept


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
    request: Request = None,
):
    """Inhabilitar un departamento (baja lógica).

    No se puede inhabilitar si tiene empleados activos asignados.
    """
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Departamento no encontrado"
        )
    if dept.is_active:
        in_use = (
            db.query(Employee)
            .filter(
                Employee.is_active == True,  # noqa: E712
                Employee.department.ilike(dept.name),
            )
            .count()
        )
        if in_use > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede inhabilitar: {in_use} empleado(s) activo(s) pertenecen a este departamento",
            )
        dept.is_active = False
        db.commit()
        log_audit(
            db=db,
            user_id=current_user.id,
            action="disable_department",
            entity_type="department",
            entity_id=dept.id,
            details={"name": dept.name},
            request=request,
        )
    return None
