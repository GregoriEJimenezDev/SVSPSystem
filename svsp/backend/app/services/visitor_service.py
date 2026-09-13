import base64
import io
import json

import qrcode
from sqlalchemy.orm import Session

from app.models.visitor import Visitor, VisitorStatus
from app.repositories.visitor_repository import VisitorRepository
from app.schemas.visitor import VisitorCreate


class VisitorNotFoundError(Exception):
    pass


class VisitorService:
    """Registro de visitantes y generacion/verificacion de su codigo QR.
    El QR codifica el id, nombre y cedula del visitante para poder
    verificarlo posteriormente en porteria.
    """

    def __init__(self, db: Session):
        self.repo = VisitorRepository(db)

    def register(self, data: VisitorCreate) -> tuple[Visitor, str]:
        visitor = Visitor(
            first_name=data.first_name,
            last_name=data.last_name,
            cedula=data.cedula,
        )
        visitor = self.repo.add(visitor)
        qr_base64 = self._generate_qr(visitor)
        return visitor, qr_base64

    def _generate_qr(self, visitor: Visitor) -> str:
        payload = json.dumps(
            {
                "visitor_id": str(visitor.id),
                "full_name": f"{visitor.first_name} {visitor.last_name}",
                "cedula": visitor.cedula,
            }
        )
        img = qrcode.make(payload)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def verify(self, visitor_id) -> Visitor:
        visitor = self.repo.get(visitor_id)
        if not visitor:
            raise VisitorNotFoundError("Visitante no encontrado")
        visitor.status = VisitorStatus.VERIFIED
        return self.repo.save(visitor)

    def search(self, term: str) -> list[Visitor]:
        return self.repo.search(term)

    def list(self) -> list[Visitor]:
        return self.repo.list()
