import uuid

from pydantic import BaseModel, ConfigDict

from app.models.employee import EmployeeStatus


class EmployeeCreate(BaseModel):
    full_name: str
    department: str


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    department: str | None = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    department: str
    status: EmployeeStatus
