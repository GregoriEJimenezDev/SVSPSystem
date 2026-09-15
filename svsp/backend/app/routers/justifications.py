import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_module
from app.schemas.justification import JustificationCreate, JustificationOut
from app.services.justification_service import JustificationService

router = APIRouter(
    prefix="/api/justifications",
    tags=["Justificaciones"],
    dependencies=[Depends(require_module("asistencia"))],
)


@router.post("/", response_model=JustificationOut)
def create_justification(payload: JustificationCreate, db: Session = Depends(get_db)):
    return JustificationService(db).create(payload)


@router.get("/employee/{employee_id}", response_model=list[JustificationOut])
def list_by_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return JustificationService(db).list_by_employee(employee_id)
