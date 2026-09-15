import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.justification import JustificationType


class JustificationCreate(BaseModel):
    employee_id: uuid.UUID
    type: JustificationType
    start_date: date
    end_date: date
    notes: str | None = None


class JustificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    type: JustificationType
    start_date: date
    end_date: date
    notes: str | None
