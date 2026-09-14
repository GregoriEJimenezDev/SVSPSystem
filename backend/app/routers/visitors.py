from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.models import Visitor, User
from core.schemas import VisitorCreate, VisitorResponse, VisitorQRResponse
from core.dependencies import get_current_active_user, log_audit
import qrcode
import base64
from io import BytesIO
from datetime import datetime


router = APIRouter(prefix="/api/v1/visitors", tags=["Visitas"])


@router.post("/", response_model=VisitorResponse, status_code=status.HTTP_201_CREATED)
def register_visitor(
    visitor_data: VisitorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
):
    """Registrar nuevo visitante"""
    # Verificar si ya existe con mismo documento
    existing = (
        db.query(Visitor)
        .filter(Visitor.document_number == visitor_data.document_number)
        .first()
    )

    if existing:
        # Actualizar fecha de última visita
        existing.verified_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)

        # Log de auditoría
        log_audit(
            db=db,
            user_id=current_user.id,
            action="update_visitor",
            entity_type="visitor",
            entity_id=existing.id,
            details={
                "first_name": existing.first_name,
                "last_name": existing.last_name,
            },
            request=request,
        )

        return existing

    new_visitor = Visitor(
        first_name=visitor_data.first_name,
        last_name=visitor_data.last_name,
        document_number=visitor_data.document_number,
        is_verified=False,
    )

    db.add(new_visitor)
    db.commit()
    db.refresh(new_visitor)

    # Generar QR de verificación
    qr_data = f"visitor_id:{new_visitor.id}|name:{new_visitor.first_name} {new_visitor.last_name}|doc:{new_visitor.document_number}"
    qr_img = qrcode.make(qr_data)
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="register_visitor",
        entity_type="visitor",
        entity_id=new_visitor.id,
        details={
            "first_name": new_visitor.first_name,
            "last_name": new_visitor.last_name,
        },
        request=request,
    )

    return VisitorResponse(
        id=new_visitor.id,
        first_name=new_visitor.first_name,
        last_name=new_visitor.last_name,
        document_number=new_visitor.document_number,
        is_verified=new_visitor.is_verified,
        verified_at=new_visitor.verified_at,
        created_at=new_visitor.created_at,
        qr_base64=qr_base64,
    )


@router.get("/{visitor_id}", response_model=VisitorResponse)
def get_visitor(
    visitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtener visitante por ID"""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visitante no encontrado"
        )
    return visitor


@router.post("/{visitor_id}/verify", response_model=VisitorResponse)
def verify_visitor(
    visitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Verificar visitante (al escanear QR)"""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visitante no encontrado"
        )

    visitor.is_verified = True
    visitor.verified_at = datetime.utcnow()
    db.commit()
    db.refresh(visitor)

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="verify_visitor",
        entity_type="visitor",
        entity_id=visitor.id,
        details={"is_verified": visitor.is_verified},
        request=None,
    )

    return visitor


@router.get("/", response_model=List[VisitorResponse])
def list_visitors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Listar todos los visitantes"""
    visitors = db.query(Visitor).offset(skip).limit(limit).all()
    return visitors
