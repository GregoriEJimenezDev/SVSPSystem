from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import HTMLResponse, StreamingResponse
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
import xlrd
from xlrd import xldate_as_datetime
import qrcode
import base64
from io import BytesIO
from datetime import date, time, datetime, timedelta

router = APIRouter(prefix="/api/v1/attendance", tags=["Asistencia"])


# ---------------------------------------------------------------------------
# Lectura de planillas: .xlsx (openpyxl) y .xls (xlrd, p. ej. reportes ZKTeco)
# ---------------------------------------------------------------------------

def _cell_str(value):
    """Normaliza una celda a texto (o None si vacía)."""
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    s = str(value).strip()
    return s or None


def _read_xlsx(contents: bytes):
    """Devuelve [(nombre_hoja, filas)] donde filas[0] es el encabezado."""
    wb = openpyxl.load_workbook(BytesIO(contents), data_only=True, read_only=True)
    tables = []
    try:
        for ws in wb.worksheets:
            rows = [[c.value for c in row] for row in ws.iter_rows()]
            tables.append((ws.title or "", rows))
    finally:
        wb.close()
    return tables


def _read_xls(contents: bytes):
    """Devuelve [(nombre_hoja, filas)] convirtiendo fechas numéricas."""
    book = xlrd.open_workbook(file_contents=contents)
    tables = []
    for sh in book.sheets():
        rows = []
        for r in range(sh.nrows):
            row = []
            for c in range(sh.ncols):
                ctype = sh.cell_type(r, c)
                value = sh.cell_value(r, c)
                if ctype == xlrd.XL_CELL_DATE:
                    try:
                        value = xldate_as_datetime(value, book.datemode)
                    except Exception:
                        pass
                row.append(value)
            rows.append(row)
        tables.append((sh.name or "", rows))
    return tables


def _read_spreadsheet(contents: bytes, filename: str):
    """Lee .xlsx u .xls y devuelve [(hoja, filas)]. Lanza 400 si es inválido."""
    name = (filename or "").lower()
    readers = (
        (_read_xlsx, _read_xls) if name.endswith(".xlsx") else (_read_xls, _read_xlsx)
    )
    last_error: Exception | None = None
    for reader in readers:
        try:
            tables = reader(contents)
            if any(len(rows) > 1 for _, rows in tables):
                return tables
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001 - se intenta el otro formato
            last_error = exc
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Archivo inválido. Se esperaba un archivo Excel (.xls o .xlsx)",
    )


def _norm_header(value) -> str:
    return (
        _cell_str(value).lower().replace("_", " ").replace("-", " ").replace(".", " ")
        if _cell_str(value)
        else ""
    )


def _merge_zkteco_header(rows, idx: int):
    """Combina encabezado + sub-encabezados (formato ZKTeco: On-duty/Off-duty
    en la fila siguiente). Devuelve (encabezados, filas_consumidas)."""
    headers = [_norm_header(v) for v in rows[idx]]
    consumed = 1
    if idx + 1 < len(rows):
        nxt = [_norm_header(v) for v in rows[idx + 1]]
        if any("on duty" in h or "off duty" in h for h in nxt):
            merged = []
            width = max(len(headers), len(nxt))
            for i in range(width):
                parent = headers[i] if i < len(headers) else ""
                sub = nxt[i] if i < len(nxt) else ""
                merged.append(f"{parent} {sub}".strip())
            headers, consumed = merged, 2
    return headers, consumed


def _detect_columns(headers: list[str]):
    """Mapea encabezados a índices. Devuelve dict o None si no calza."""
    exact = {
        "empleado": "empleado",
        "nombre": "empleado",
        "name": "empleado",
        "hora entrada": "entrada",
        "horaentrada": "entrada",
        "hora de entrada": "entrada",
        "entrada": "entrada",
        "check in": "entrada",
        "hora salida": "salida",
        "horasalida": "salida",
        "hora de salida": "salida",
        "salida": "salida",
        "check out": "salida",
        "department": "depto",
        "departamento": "depto",
        "dept": "depto",
        "depto": "depto",
        "date": "fecha",
        "fecha": "fecha",
    }
    mapping: dict[str, int] = {}
    for i, h in enumerate(headers):
        key = exact.get(h.replace("  ", " ").strip())
        if key and key not in mapping:
            mapping[key] = i
    # Fallback ZKTeco: primera columna que contenga cada marcador
    if "entrada" not in mapping:
        for i, h in enumerate(headers):
            if "on duty" in h:
                mapping["entrada"] = i
                break
    if "salida" not in mapping:
        for i, h in enumerate(headers):
            if "off duty" in h:
                mapping["salida"] = i
                break
    if "empleado" not in mapping:
        return None
    if "entrada" not in mapping or "salida" not in mapping:
        return None
    return mapping


def _find_table(tables):
    """Busca en todas las hojas la primera tabla con columnas reconocibles."""
    for sheet_name, rows in tables:
        if not rows:
            continue
        for idx in range(min(12, len(rows))):
            headers, consumed = _merge_zkteco_header(rows, idx)
            mapping = _detect_columns(headers)
            if mapping:
                return sheet_name, headers, mapping, rows[idx + consumed :]
    return None


def _parse_record_date(value):
    """Devuelve date o None. Acepta datetime/date, 'YYYY-MM-DD' y 'DD/MM/YYYY'."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_time(value):
    """Devuelve time o None. Acepta 'HH:MM[:SS]', datetime y objetos con .hour."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.time()
    if hasattr(value, "hour") and not isinstance(value, str):
        try:
            return time(value.hour, value.minute, getattr(value, "second", 0))
        except (ValueError, TypeError):
            return None
    if isinstance(value, str):
        parts = value.strip().split(":")
        try:
            return time(
                int(parts[0]) if len(parts) > 0 else 0,
                int(parts[1]) if len(parts) > 1 else 0,
                int(parts[2]) if len(parts) > 2 else 0,
            )
        except (ValueError, IndexError):
            return None
    return None


@router.post("/import-excel", response_model=ExcelImportResult)
def import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Importar archivo del ponchador biométrico (.xls o .xlsx).

    Formatos aceptados:
    - Planilla simple con columnas Empleado, Hora_entrada, Hora_salida.
    - Reporte ZKTeco StandardReport (.xls): se usa la hoja con registros
      por día (Name, Department, Date, On-duty, Off-duty).
    """
    # Leer archivo (se acepta .xls y .xlsx por extensión o contenido)
    filename = (file.filename or "").lower()
    if filename and not (filename.endswith(".xls") or filename.endswith(".xlsx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo inválido. Se esperaba un archivo Excel (.xls o .xlsx)",
        )
    contents = file.file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo inválido. Se esperaba un archivo Excel (.xls o .xlsx)",
        )
    tables = _read_spreadsheet(contents, filename)

    found = _find_table(tables)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No se encontraron columnas reconocibles. Se esperaba "
                "Empleado/Hora_entrada/Hora_salida o un reporte ZKTeco "
                "(Name/Department/Date/On-duty/Off-duty)."
            ),
        )
    sheet_name, headers, mapping, data_rows = found

    processed = 0
    created = 0
    updated = 0
    errors = []

    for row_idx, raw_row in enumerate(data_rows, start=2):
        processed += 1
        try:
            row = list(raw_row) + [None] * (len(headers) - len(list(raw_row)))
            # Mapear datos por encabezado
            empleado_nombre = _cell_str(row[mapping["empleado"]])
            hora_entrada = row[mapping["entrada"]]
            hora_salida = row[mapping["salida"]]
            departamento = (
                _cell_str(row[mapping["depto"]]) if "depto" in mapping else None
            )
            fecha_registro = (
                _parse_record_date(row[mapping["fecha"]])
                if "fecha" in mapping
                else None
            ) or date.today()

            if not empleado_nombre:
                errors.append(f"Fila {row_idx}: Nombre de empleado vacío")
                continue

            # Buscar o crear empleado
            employee = (
                db.query(Employee)
                .filter(Employee.name.ilike(empleado_nombre))
                .first()
            )

            if not employee:
                # Crear automáticamente
                employee = Employee(
                    name=empleado_nombre,
                    department=departamento,
                    is_active=True,
                )
                db.add(employee)
                db.commit()
                db.refresh(employee)
                created += 1
            else:
                if departamento and employee.department != departamento:
                    employee.department = departamento
                updated += 1

            # Parsear horas (formato time, datetime o string)
            check_in = _parse_time(hora_entrada)
            check_out = _parse_time(hora_salida)
            total_hours = None

            # Calcular total de horas si tenemos ambas
            if check_in and check_out:
                dt_in = datetime.combine(date.today(), check_in)
                dt_out = datetime.combine(date.today(), check_out)
                diff = dt_out - dt_in
                total_hours = str(round(diff.total_seconds() / 3600, 2))

            # Verificar si ya existe registro para este empleado en esa fecha
            # (usa la fecha del reporte cuando viene incluida, si no la de hoy)
            existing_attendance = (
                db.query(Attendance)
                .filter(
                    Attendance.employee_id == employee.id,
                    Attendance.date == fecha_registro,
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
                    date=fecha_registro,
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
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Listar registros de asistencia con filtros"""
    query = db.query(Attendance)

    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)

    if department:
        query = query.join(Employee, Attendance.employee_id == Employee.id).filter(
            Employee.department.ilike(f"%{department.strip()}%")
        )

    if start_date:
        query = query.filter(Attendance.date >= start_date)

    if end_date:
        query = query.filter(Attendance.date <= end_date)

    attendances = query.order_by(Attendance.date.desc()).all()
    return attendances


# Hora límite de llegada: entradas posteriores cuentan como tardanza.
LATE_AFTER = time(8, 0)


def _day_presence(records, ref_day, total_active: int):
    """Presentes/ausentes/tardanzas coherentes para un día.

    Presentes = empleados DISTINTOS con hora de entrada (nunca supera el
    total de empleados). Ausentes = total − presentes (mínimo 0).
    """
    present_ids = {
        r.employee_id for r in records if r.date == ref_day and r.check_in is not None
    }
    late_ids = {
        r.employee_id
        for r in records
        if r.date == ref_day and r.check_in is not None and r.check_in > LATE_AFTER
    }
    present = len(present_ids)
    absent = max(0, total_active - present)
    return present, absent, len(late_ids)


@router.get("/stats", response_model=AttendanceStats)
def attendance_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    employee_id: Optional[int] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Estadísticas de asistencia.

    Reglas coherentes (presentes nunca supera el total de empleados):
    - Se calculan sobre un DÍA de referencia: end_date, o start_date,
      o hoy si no hay rango.
    - Presentes = empleados DISTINTOS con hora de entrada ese día.
    - Ausentes = empleados activos − presentes (nunca negativo).
    - Tardanzas = presentes con entrada posterior a las 08:00.
    - Respeta los filtros de empleado y departamento.
    """
    filters = {
        "employee_id": employee_id,
        "department": department,
        "start_date": str(start_date) if start_date else None,
        "end_date": str(end_date) if end_date else None,
    }
    records = _apply_report_filters(db.query(Attendance), filters, db).all()
    ref_day = end_date or start_date or date.today()

    emp_query = db.query(Employee).filter(Employee.is_active == True)  # noqa: E712
    if department:
        emp_query = emp_query.filter(Employee.department.ilike(f"%{department.strip()}%"))
    if employee_id:
        emp_query = emp_query.filter(Employee.id == employee_id)
    total_employees = emp_query.count()

    present, absent, late = _day_presence(records, ref_day, total_employees)

    # Promedio de horas del día de referencia (total_hours se guarda como texto)
    hours = []
    for r in records:
        if r.date != ref_day or r.total_hours is None:
            continue
        try:
            hours.append(float(str(r.total_hours).strip()))
        except (ValueError, TypeError):
            continue
    avg_hours = round(sum(hours) / len(hours), 2) if hours else 0.0

    return AttendanceStats(
        total_employees=total_employees,
        present_today=present,
        absent_today=absent,
        late_today=late,
        total_hours=avg_hours,
    )


@router.get("/chart-data", response_model=AttendanceChartData)
def attendance_chart_data(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Datos para gráfico de distribución de asistencia.

    Misma lógica coherente que /stats: conteo por empleados distintos
    del día de referencia (último con datos en el rango, o el fin del
    rango, o hoy).
    """
    query = db.query(Attendance)

    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)

    records = query.all()
    last_record = query.order_by(Attendance.date.desc()).first()
    if last_record is not None and last_record.date is not None:
        chart_date = last_record.date
    elif end_date:
        chart_date = end_date
    elif start_date:
        chart_date = start_date
    else:
        chart_date = date.today()

    total_active = db.query(Employee).filter(Employee.is_active == True).count()  # noqa: E712
    present_count, absent_count, late_count = _day_presence(records, chart_date, total_active)

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


@router.post("/report-docx")
def download_report_docx(
    payload: ReportQRRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_module("asistencia")),
):
    """Descargar reporte de asistencia en Word editable (.docx).

    Usa los mismos filtros que el reporte QR: empleado, departamento,
    rango de fechas. Columnas: Empleado, Hora de entrada, Hora salida,
    Total horas trabajadas.
    """
    from docx import Document
    from docx.shared import Pt

    filters = {
        "employee_id": payload.employee_id,
        "department": payload.department,
        "start_date": str(payload.start_date) if payload.start_date else None,
        "end_date": str(payload.end_date) if payload.end_date else None,
    }
    query = db.query(Attendance)
    records = _apply_report_filters(query, filters, db).all()

    doc = Document()
    style = doc.styles["Normal"]
    style.font.size = Pt(11)
    doc.add_heading("SVSP - Reporte de Asistencia", level=1)
    periodo = f"{filters['start_date'] or '...'} al {filters['end_date'] or '...'}"
    doc.add_paragraph(f"Periodo: {periodo}")
    if filters["department"]:
        doc.add_paragraph(f"Departamento: {filters['department']}")
    doc.add_paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  "
        f"Total registros: {len(records)}"
    )

    table = doc.add_table(rows=1, cols=4)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text = "Empleado"
    hdr[1].text = "Hora de entrada"
    hdr[2].text = "Hora salida"
    hdr[3].text = "Total horas trabajadas"
    for record in records:
        emp = db.query(Employee).filter(Employee.id == record.employee_id).first()
        cells = table.add_row().cells
        cells[0].text = emp.name if emp else f"#{record.employee_id}"
        cells[1].text = (
            record.check_in.strftime("%H:%M") if record.check_in else "-"
        )
        cells[2].text = (
            record.check_out.strftime("%H:%M") if record.check_out else "-"
        )
        cells[3].text = str(record.total_hours) if record.total_hours else "-"

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="download_report_docx",
        entity_type="attendance",
        entity_id=0,
        details={**filters, "total": len(records)},
        request=None,
    )

    stamp = date.today().strftime("%Y%m%d")
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=reporte-asistencia-{stamp}.docx"
        },
    )


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
