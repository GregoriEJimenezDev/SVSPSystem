from datetime import date

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_module
from app.schemas.attendance import AttendanceImportSummary, AttendanceOut
from app.services.attendance_service import AttendanceService

router = APIRouter(
    prefix="/api/attendance",
    tags=["Asistencia"],
    dependencies=[Depends(require_module("asistencia"))],
)


@router.post("/import", response_model=AttendanceImportSummary)
async def import_attendance(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    result = AttendanceService(db).import_from_excel(content)
    return AttendanceImportSummary(**result)


@router.get("/", response_model=list[AttendanceOut])
def list_attendance(
    start: date = Query(...),
    end: date = Query(...),
    db: Session = Depends(get_db),
):
    return AttendanceService(db).list_between(start, end)
