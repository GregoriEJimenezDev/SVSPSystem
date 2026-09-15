import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    work_date: date
    check_in: datetime | None
    check_out: datetime | None
    total_hours: float | None


class AttendanceImportSummary(BaseModel):
    rows_processed: int
    employees_created: int
    attendances_created: int
