from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db
from app.schemas import (
    VisitorCreate,
    VisitorUpdate,
    VisitorResponse,
)
from app.services import get_visitor_service
from app.dependencies import get_current_active_user
from app.models import User

router = APIRouter(prefix="/visitors", tags=["Visitors"])


@router.post("/", response_model=VisitorResponse, status_code=201)
def create_visitor(
    visitor: VisitorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_visitor_service(db)
    return svc.create_visitor(visitor)


@router.get("/", response_model=List[VisitorResponse])
def list_visitors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_visitor_service(db)
    return svc.get_all_active()


@router.get("/search", response_model=List[VisitorResponse])
def search_by_name(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_visitor_service(db)
    return svc.search_by_name(name)


@router.get("/cedula/{cedula}", response_model=VisitorResponse)
def get_by_cedula(
    cedula: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_visitor_service(db)
    result = svc.get_by_cedula(cedula)
    if not result:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    return result