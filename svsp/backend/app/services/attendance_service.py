from datetime import date, datetime, timedelta

import openpyxl
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.repositories.attendance_repository import AttendanceRepository
from app.services.employee_service import EmployeeService


class AttendanceService:
    """Procesa el archivo Excel del poncher y expone consultas de
    asistencia para reportes y graficos.
    """

    def __init__(self, db: Session):
        self.repo = AttendanceRepository(db)
        self.employee_service = EmployeeService(db)

    def import_from_excel(self, file_bytes: bytes) -> dict:
        """Espera columnas (en cualquier orden, por encabezado):
        Empleado | Hora de entrada | Hora de salida | Horas totales trabajadas
        """
        workbook = openpyxl.load_workbook(filename=__import__("io").BytesIO(file_bytes), data_only=True)
        sheet = workbook.active

        headers = [str(cell.value).strip().lower() if cell.value else "" for cell in sheet[1]]

        def col_index(*names: str) -> int | None:
            for name in names:
                if name in headers:
                    return headers.index(name)
            return None

        idx_employee = col_index("empleado", "employee")
        idx_check_in = col_index("hora de entrada", "check_in", "entrada")
        idx_check_out = col_index("hora de salida", "check_out", "salida")
        idx_total_hours = col_index("horas totales trabajadas", "horas totales", "total_hours")

        employees_created = 0
        attendances_created = 0

        for row in sheet.iter_rows(min_row=2, values_only=True):
            if idx_employee is None or row[idx_employee] in (None, ""):
                continue

            employee_name = str(row[idx_employee]).strip()
            employee, created = self.employee_service.get_or_create_by_name(employee_name)
            if created:
                employees_created += 1

            check_in = row[idx_check_in] if idx_check_in is not None else None
            check_out = row[idx_check_out] if idx_check_out is not None else None
            total_hours = row[idx_total_hours] if idx_total_hours is not None else None

            work_date = check_in.date() if isinstance(check_in, datetime) else date.today()

            attendance = Attendance(
                employee_id=employee.id,
                work_date=work_date,
                check_in=check_in if isinstance(check_in, datetime) else None,
                check_out=check_out if isinstance(check_out, datetime) else None,
                total_hours=float(total_hours) if isinstance(total_hours, (int, float)) else None,
            )
            self.repo.add(attendance)
            attendances_created += 1

        return {
            "rows_processed": attendances_created,
            "employees_created": employees_created,
            "attendances_created": attendances_created,
        }

    def list_between(self, start: date, end: date) -> list[Attendance]:
        return self.repo.list_between(start, end)

    def purge_old_reports(self, retention_days: int) -> int:
        """Elimina reportes de asistencia con mas de `retention_days` dias,
        segun la regla de retencion de 2 semanas definida para el sistema.
        """
        cutoff = date.today() - timedelta(days=retention_days)
        return self.repo.delete_older_than(cutoff)
