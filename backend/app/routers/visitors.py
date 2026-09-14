from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List

from fastapi.responses import HTMLResponse
from core.database import get_db
from core.models import Visitor, User
from core.schemas import VisitorCreate, VisitorResponse, VisitorQRResponse
from core.dependencies import require_module, log_audit
from core.config import get_settings
import qrcode
import base64
from io import BytesIO
from datetime import datetime


router = APIRouter(prefix="/api/v1/visitors", tags=["Visitas"])

settings = get_settings()


def build_visitor_qr(visitor: Visitor) -> tuple[str, str]:
    """Genera la URL pública y el QR en base64 para un visitante."""
    url = f"{settings.public_base_url}/api/v1/visitors/public/{visitor.id}"
    qr_img = qrcode.make(url)
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return url, qr_base64


@router.post("/", response_model=VisitorQRResponse, status_code=status.HTTP_201_CREATED)
def register_visitor(
    visitor_data: VisitorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("visitas")),
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

        url, qr_base64 = build_visitor_qr(existing)
        return VisitorQRResponse(
            qr_base64=qr_base64,
            visitor=VisitorResponse.model_validate(existing),
        )

    new_visitor = Visitor(
        first_name=visitor_data.first_name,
        last_name=visitor_data.last_name,
        document_number=visitor_data.document_number,
        is_verified=False,
    )

    db.add(new_visitor)
    db.commit()
    db.refresh(new_visitor)

    # Generar QR apuntando a la ficha pública del visitante
    url, qr_base64 = build_visitor_qr(new_visitor)

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

    return VisitorQRResponse(
        qr_base64=qr_base64,
        visitor=VisitorResponse.model_validate(new_visitor),
    )


@router.get("/{visitor_id}", response_model=VisitorResponse)
def get_visitor(
    visitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("visitas")),
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
    current_user: User = Depends(require_module("visitas")),
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
    current_user: User = Depends(require_module("visitas")),
):
    """Listar todos los visitantes"""
    visitors = db.query(Visitor).offset(skip).limit(limit).all()
    return visitors


@router.get("/{visitor_id}/qr", response_model=VisitorQRResponse)
def get_visitor_qr(
    visitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("visitas")),
):
    """Obtener el QR de un visitante ya registrado"""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visitante no encontrado"
        )
    url, qr_base64 = build_visitor_qr(visitor)
    return VisitorQRResponse(
        qr_base64=qr_base64,
        visitor=VisitorResponse.model_validate(visitor),
    )


@router.get("/public/{visitor_id}", response_class=HTMLResponse)
def public_visitor_card(visitor_id: int, db: Session = Depends(get_db)):
    """Ficha pública del visitante (se abre al escanear el QR, sin login)."""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visitante no encontrado"
        )
    estado = "VERIFICADO" if visitor.is_verified else "REGISTRADO"
    color = "#1e7e34" if visitor.is_verified else "#B8912F"
    fecha = visitor.created_at.strftime("%d/%m/%Y %H:%M") if visitor.created_at else "-"
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SVSP - Verificación de visitante</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'Segoe UI',sans-serif;background:#faf8f3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.card{{background:#fff;border:1px solid #f0e6cf;border-radius:20px;padding:40px 32px;max-width:420px;width:100%;box-shadow:0 16px 40px rgba(180,140,40,.15);text-align:center}}
.badge{{display:inline-block;padding:8px 20px;border-radius:20px;color:#fff;font-weight:700;font-size:15px;background:{color};margin:16px 0 24px}}
h1{{font-size:24px;color:#2c2c2c;margin-bottom:4px}}p.sub{{color:#8a8a8a;font-size:15px;margin-bottom:8px}}
.row{{display:flex;justify-content:space-between;padding:12px 4px;border-top:1px solid #f0e6cf;font-size:16px}}
.row span:first-child{{color:#8a8a8a}}.row span:last-child{{font-weight:600;color:#2c2c2c}}</style>
</head><body><div class="card">
<h1>SVSP - Control de Visitas</h1><p class="sub">Verificación de identidad</p>
<div class="badge">{estado}</div>
<div class="row"><span>Nombre</span><span>{visitor.first_name} {visitor.last_name}</span></div>
<div class="row"><span>Cédula</span><span>{visitor.document_number}</span></div>
<div class="row"><span>Registro</span><span>{fecha}</span></div>
</div></body></html>"""
