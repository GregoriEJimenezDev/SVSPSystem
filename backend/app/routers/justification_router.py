from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db
from app.schemas import (
    JustificationCreate,
    JustificationUpdate,
    JustificationResponse,
)
from app.services import get_justification_service
from app.dependencies import get_current_active_user
from datetime import datetime
from app.models import User

router = APIRouter(prefix="/justifications", tags=["Justifications"])


@router.post("/", response_model=JustificationResponse, status_code=201)
def create_justification(
    data: JustificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_justification_service(db)
    return svc.create_justification(data)


@router.get("/employee/{employee_id}", response_model=List[JustificationResponse])
def get_by_employee(
    employee_id: int,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_justification_service(db)
    return svc.get_employee_justifications(employee_id, start_date, end_date)


@router.get("/type/{jtype}", response_model=List[JustificationResponse])
def get_by_type(
    jtype: str,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_justification_service(db)
    return svc.get_justifications_by_type(jtype, start_date, end_date)


@router.get("/period", response_model=List[JustificationResponse])
def get_by_period(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_justification_service(db)
    return svc.get_all_active(start_date, end_date)