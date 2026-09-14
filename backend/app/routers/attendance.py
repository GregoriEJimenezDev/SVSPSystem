from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
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
)
from core.dependencies import get_current_active_user, log_audit
import openpyxl
from datetime import date, time, datetime

router = APIRouter(prefix="/api/v1/attendance", tags=["Asistencia"])


@router.post("/import-excel", response_model=ExcelImportResult)
def import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Importar archivo Excel del poncher biométrico"""
    # Validar tipo de archivo
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo debe ser .xlsx"
        )

    # Leer archivo
    contents = file.file.read()
    wb = openpyxl.load_workbook(contents, data_only=True)
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
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_active_user),
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
