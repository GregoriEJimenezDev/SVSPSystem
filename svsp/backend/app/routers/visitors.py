import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_module
from app.schemas.visitor import VisitorCreate, VisitorOut, VisitorRegisterResponse
from app.services.visitor_service import VisitorNotFoundError, VisitorService

router = APIRouter(
    prefix="/api/visitors",
    tags=["Visitas"],
    dependencies=[Depends(require_module("visitas"))],
)


@router.post("/", response_model=VisitorRegisterResponse)
def register_visitor(payload: VisitorCreate, db: Session = Depends(get_db)):
    visitor, qr_base64 = VisitorService(db).register(payload)
    return VisitorRegisterResponse(visitor=visitor, qr_code_base64=qr_base64)


@router.get("/", response_model=list[VisitorOut])
def list_visitors(q: str | None = Query(default=None), db: Session = Depends(get_db)):
    service = VisitorService(db)
    return service.search(q) if q else service.list()


@router.post("/{visitor_id}/verify", response_model=VisitorOut)
def verify_visitor(visitor_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return VisitorService(db).verify(visitor_id)
    except VisitorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
