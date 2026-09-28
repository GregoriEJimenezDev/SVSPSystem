from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db
from app.schemas import (
    AttendanceCreate,
    AttendanceResponse,
)
from app.services import get_attendance_service
from app.dependencies import get_current_active_user
from datetime import datetime
from app.models import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/check-in", response_model=AttendanceResponse, status_code=201)
def check_in(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_attendance_service(db)
    return svc.check_in(employee_id)


@router.post("/check-out", response_model=AttendanceResponse)
def check_out(
    employee_id: int,
    check_out_time: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = get_attendance_service(db)
    return svc.check_out(employee_id, check_out_time)


@router.post("/import-excel", status_code=201)
def import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    import pandas as pd
    import io
    from openpyxl import load_workbook
    from app.models import Employee, Attendance
    from app.repositories import EmployeeRepository, AttendanceRepository
    from passlib.context import CryptContext
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Solo se aceptan archivos .xlsx o .xls",
        )
    
    # Sanitize: read with openpyxl/pandas and validate structure
    try:
        wb = load_workbook(io.BytesIO(contents), read_only=True)
        sheet = wb.active
        
        # Read all rows
        rows = []
        for row in sheet.iter_rows(values_only=True):
            rows.append(row)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al leer el archivo Excel: {str(e)}",
        )
    
    if not rows or len(rows) < 2:
        raise HTTPException(
            status_code=400,
            detail="El archivo Excel no tiene datos suficientes",
        )
    
    # Process rows - assume: Col A=Nombre, Col B=Departamento, Col C=Fecha/Hora
    employees_created = 0
    employees_updated = 0
    records_created = 0
    
    # Get existing employees
    emp_repo = EmployeeRepository(db)
    existing_employees = {e.name.lower(): e for e in emp_repo.get_all_active()}
    
    attendance_repo = AttendanceRepository(db)
    
    for row in rows[1:]:  # skip header
        name = row[0] if len(row) > 0 else None
        department = row[1] if len(row) > 1 else None
        fecha_hora = row[2] if len(row) > 2 else None
        
        if not name:
            continue
        
        # Normalize name
        name_str = str(name).strip()
        dept_str = str(department).strip() if department else None
        fecha_str = str(fecha_hora).strip() if fecha_hora else None
        
        # Get or create employee
        emp_key = name_str.lower()
        if emp_key in existing_employees:
            emp = existing_employees[emp_key]
            employees_updated += 1
            # Update department if changed
            if emp.department != dept_str:
                emp.department = dept_str
                db.commit()
        else:
            # Auto-create employee
            from app.services import get_employee_service
            svc = get_employee_service(db)
            # Create user first
            user_created = svc.user_repo.create(
                UserCreate(
                    email=f"{name_str.lower().replace(' ', '.')}@svsp.local",
                    full_name=name_str,
                )
            )
            emp = svc.emp_repo.create_with_user(user_created.id, EmployeeCreate(name=name_str, department=dept_str))
            employees_created += 1
            existing_employees[emp_key] = emp
        
        # Create attendance record
        # Parse date - handle various formats
        try:
            from datetime import datetime
            # Try different date formats
            check_in_dt = datetime.now()
            if fecha_str:
                # Try common formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M"]:
                    try:
                        check_in_dt = datetime.strptime(fecha_str, fmt)
                        break
                    except ValueError:
                        continue
            
            attendance_repo.create(AttendanceCreate(employee_id=emp.id))
            records_created += 1
        except Exception as e:
            # Log but continue
            print(f"Error creating attendance for {name_str}: {e}")
            continue
    
    db.commit()
    
    return {
        "empleadosCreados": employees_created,
        "duplicadosActualizados": employees_updated,
        "totalRegistros": records_created,
    }