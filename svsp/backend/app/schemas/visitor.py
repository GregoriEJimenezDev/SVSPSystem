import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.visitor import VisitorStatus


class VisitorCreate(BaseModel):
    first_name: str
    last_name: str
    cedula: str


class VisitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    cedula: str
    status: VisitorStatus
    registered_at: datetime


class VisitorRegisterResponse(BaseModel):
    visitor: VisitorOut
    qr_code_base64: str
