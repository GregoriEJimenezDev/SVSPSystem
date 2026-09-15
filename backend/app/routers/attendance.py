from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.models import Employee, Attendance, Justification, User
from core.schemas import (
    AttendanceResponse,
    AttendanceCreate,
    ExcelImportResult,
    AttendanceStats,
    AttendanceChartData,
    ReportQRRequest,
    ReportQRResponse,
)
from core.dependencies import require_module, log_audit
from core.security import create_access_token, decode_token
from core.config import get_settings
import openpyxl
import qrcode
import base64
from io import BytesIO
from datetime import date, time, datetime, timedelta

router = APIRouter(prefix="/api/v1/attendance", tags=["Asistencia"])


@router.post("/import-excel", response_model=ExcelImportResult)
def import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Importar archivo del poncher biométrico"""
    # Leer archivo
    contents = file.file.read()
    try:
        wb = openpyxl.load_workbook(contents, data_only=True)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo inválido. Se esperaba un archivo Excel (.xlsx)",
        )
    ws = wb.active

    # Leer encabezados por nombre de columna (no posición fija)
    headers = [cell.value for cell in ws[1]]
    header_map = {str(h).strip().lower(): i for i, h in enumerate(headers)}

    required_cols = ["empleado", "hora_entrada", "hora_salida"]
    for col in required_cols:
        if col not in header_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Columna requerida '{col}' no encontrada en el Excel",
            )

    processed = 0
    created = 0
    updated = 0
    errors = []

    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        processed += 1
        try:
            # Mapear datos por encabezado
            empleado_nombre = row[header_map.get("empleado", 0)]
            hora_entrada = row[header_map.get("hora_entrada", 1)]
            hora_salida = row[header_map.get("hora_salida", 2)]

            if not empleado_nombre:
                errors.append(f"Fila {row_idx}: Nombre de empleado vacío")
                continue

            # Buscar o crear empleado
            employee = (
                db.query(Employee)
                .filter(Employee.name.ilike(str(empleado_nombre).strip()))
                .first()
            )

            if not employee:
                # Crear automáticamente
                employee = Employee(name=str(empleado_nombre).strip(), is_active=True)
                db.add(employee)
                db.commit()
                db.refresh(employee)
                created += 1
            else:
                updated += 1

            # Parsear horas (formato time o string)
            check_in = None
            check_out = None
            total_hours = None

            if hora_entrada:
                if isinstance(hora_entrada, str):
                    parts = hora_entrada.split(":")
                    check_in = time(
                        int(parts[0]) if len(parts) > 0 else 0,
                        int(parts[1]) if len(parts) > 1 else 0,
                    )
                elif hasattr(hora_entrada, "hour"):
                    check_in = hora_entrada.time()

            if hora_salida:
                if isinstance(hora_salida, str):
                    parts = hora_salida.split(":")
                    check_out = time(
                        int(parts[0]) if len(parts) > 0 else 0,
                        int(parts[1]) if len(parts) > 1 else 0,
                    )
                elif hasattr(hora_salida, "hour"):
                    check_out = hora_salida.time()

            # Calcular total de horas si tenemos ambas
            if check_in and check_out:
                dt_in = datetime.combine(date.today(), check_in)
                dt_out = datetime.combine(date.today(), check_out)
                diff = dt_out - dt_in
                total_hours = str(round(diff.total_seconds() / 3600, 2))

            # Verificar si ya existe registro para este empleado en el día de hoy
            today = date.today()
            existing_attendance = (
                db.query(Attendance)
                .filter(
                    Attendance.employee_id == employee.id,
                    Attendance.date == today,
                )
                .first()
            )

            if existing_attendance:
                # Actualizar registro existente
                existing_attendance.check_in = check_in
                existing_attendance.check_out = check_out
                existing_attendance.total_hours = total_hours
                existing_attendance.source = "biometrico"
                db.commit()
            else:
                # Crear nuevo registro
                new_attendance = Attendance(
                    employee_id=employee.id,
                    date=today,
                    check_in=check_in,
                    check_out=check_out,
                    total_hours=total_hours,
                    source="biometrico",
                )
                db.add(new_attendance)
                db.commit()

            updated += 1  # Counting the attendance update/creation

        except Exception as e:
            errors.append(f"Fila {row_idx}: {str(e)}")
            continue

    result = ExcelImportResult(
        processed=processed,
        created=created,
        updated=updated,
        errors=errors[:50],  # Limit error list
    )

    # Log de auditoría
    log_audit(
        db=db,
        user_id=current_user.id,
        action="import_excel",
        entity_type="attendance",
        entity_id=0,
        details={
            "processed": processed,
            "created": created,
            "errors_count": len(errors),
        },
        request=None,
    )

    return result


@router.get("/", response_model=List[AttendanceResponse])
def list_attendances(
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Listar registros de asistencia con filtros"""
    query = db.query(Attendance)

    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)

    if start_date:
        query = query.filter(Attendance.date >= start_date)

    if end_date:
        query = query.filter(Attendance.date <= end_date)

    attendances = query.order_by(Attendance.date.desc()).all()
    return attendances


@router.get("/stats", response_model=AttendanceStats)
def attendance_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Estadísticas de asistencia"""
    query = db.query(Attendance)

    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)

    records = query.all()
    total = len(records)

    # total_hours se guarda como texto: contar presente si hay hora de entrada
    present = sum(1 for r in records if r.check_in is not None)
    absent = total - present

    # Promedio de horas (parsear el texto a número cuando sea posible)
    hours = []
    for r in records:
        if r.total_hours is None:
            continue
        try:
            hours.append(float(str(r.total_hours).strip()))
        except (ValueError, TypeError):
            continue
    avg_hours = round(sum(hours) / len(hours), 2) if hours else 0.0

    total_employees = db.query(Employee).filter(Employee.is_active == True).count()

    return AttendanceStats(
        total_employees=total_employees,
        present_today=present,
        absent_today=absent,
        late_today=0,
        total_hours=avg_hours,
    )


@router.get("/chart-data", response_model=AttendanceChartData)
def attendance_chart_data(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Datos para gráfico de distribución de asistencia"""
    query = db.query(Attendance)

    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)

    records = query.all()
    present_count = sum(1 for r in records if r.check_in is not None)
    absent_count = len(records) - present_count
    late_count = 0

    # Retornar fecha del último registro para el gráfico (hoy si no hay datos)
    last_record = query.order_by(Attendance.date.desc()).first()
    if last_record is not None and last_record.date is not None:
        chart_date = last_record.date
    else:
        chart_date = date.today()

    return AttendanceChartData(
        date=chart_date, present=present_count, absent=absent_count, late=late_count
    )


def _apply_report_filters(query, filters: dict, db: Session):
    """Aplica filtros de reporte (empleado, departamento, fechas)."""
    if filters.get("employee_id"):
        query = query.filter(Attendance.employee_id == filters["employee_id"])
    if filters.get("department"):
        query = query.join(Employee, Attendance.employee_id == Employee.id).filter(
            Employee.department.ilike(f"%{filters['department']}%")
        )
    if filters.get("start_date"):
        query = query.filter(Attendance.date >= filters["start_date"])
    if filters.get("end_date"):
        query = query.filter(Attendance.date <= filters["end_date"])
    return query.order_by(Attendance.date.desc())


@router.post("/report-qr", response_model=ReportQRResponse)
def generate_report_qr(
    payload: ReportQRRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Genera un QR que abre el reporte de asistencia en el celular (sin login)."""
    settings = get_settings()
    filters = {
        "employee_id": payload.employee_id,
        "department": payload.department,
        "start_date": str(payload.start_date) if payload.start_date else None,
        "end_date": str(payload.end_date) if payload.end_date else None,
    }
    token = create_access_token(
        data={"type": "attendance_report", "filters": filters},
        expires_delta=timedelta(days=7),
    )
    url = f"{settings.public_base_url}/api/v1/attendance/public-report?token={token}"
    qr_img = qrcode.make(url)
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    log_audit(
        db=db,
        user_id=current_user.id,
        action="generate_report_qr",
        entity_type="attendance",
        entity_id=0,
        details=filters,
        request=None,
    )

    return ReportQRResponse(qr_base64=qr_base64, url=url)


@router.get("/public-report", response_class=HTMLResponse)
def public_attendance_report(token: str, db: Session = Depends(get_db)):
    """Reporte público de asistencia (se abre al escanear el QR, sin login)."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "attendance_report":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Enlace de reporte inválido o vencido",
        )
    filters = payload.get("filters", {})
    records = _apply_report_filters(db.query(Attendance), filters, db).limit(500).all()

    rows = ""
    for r in records:
        emp = db.query(Employee).filter(Employee.id == r.employee_id).first()
        nombre = emp.name if emp else f"#{r.employee_id}"
        depto = emp.department if emp and emp.department else "-"
        rows += (
            f"<div class='row'><span>{nombre} <small>{depto}</small></span>"
            f"<span>{r.date} · {r.check_in or '-'} - {r.check_out or '-'}"
            f" · {r.total_hours or '-'} h</span></div>"
        )
    if not rows:
        rows = "<p class='empty'>Sin registros para los filtros del reporte.</p>"

    periodo = (
        f"{filters.get('start_date') or '...'} al {filters.get('end_date') or '...'}"
    )
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SVSP - Reporte de asistencia</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'Segoe UI',sans-serif;background:#faf8f3;min-height:100vh;padding:20px}}
.card{{background:#fff;border:1px solid #f0e6cf;border-radius:20px;padding:28px 22px;max-width:640px;width:100%;margin:0 auto;box-shadow:0 16px 40px rgba(180,140,40,.15)}}
h1{{font-size:22px;color:#2c2c2c;text-align:center}}p.sub{{color:#8a8a8a;font-size:14px;text-align:center;margin:6px 0 20px}}
.total{{text-align:center;font-weight:700;color:#B8912F;margin-bottom:16px}}
.row{{display:flex;justify-content:space-between;gap:12px;padding:12px 4px;border-top:1px solid #f0e6cf;font-size:14px}}
.row small{{color:#8a8a8a}}.empty{{text-align:center;color:#8a8a8a;padding:20px}}</style>
</head><body><div class="card">
<h1>SVSP - Reporte de Asistencia</h1><p class="sub">Periodo: {periodo}</p>
<div class="total">Total registros: {len(records)}</div>
{rows}
</div></body></html>"""
