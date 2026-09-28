from typing import List, Optional
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session


# Repository factory functions - each creates repo with given DB session
def get_user_repo(db: Session):
    from app.repositories.user_repository import UserRepository
    return UserRepository(db)


def get_employee_repo(db: Session):
    from app.repositories.employee_repository import EmployeeRepository
    return EmployeeRepository(db)


def get_attendance_repo(db: Session):
    from app.repositories.attendance_repository import AttendanceRepository
    return AttendanceRepository(db)


def get_justification_repo(db: Session):
    from app.repositories.justification_repository import JustificationRepository
    return JustificationRepository(db)


def get_visitor_repo(db: Session):
    from app.repositories.visitor_repository import VisitorRepository
    return VisitorRepository()


# Service factory functions
def get_auth_service(db) -> "AuthService":
    from app.services.auth_service import AuthService
    from app.repositories import get_user_repo
    return AuthService(get_user_repo(db))


def get_employee_service(
    db,
    emp_repo=None,
    user_repo=None,
    att_repo=None,
    just_repo=None,
) -> "EmployeeService":
    from app.services.employee_service import EmployeeService
    if not emp_repo:
        emp_repo = get_employee_repo(db)
    if not user_repo:
        user_repo = get_user_repo(db)
    if not att_repo:
        att_repo = get_attendance_repo(db)
    if not just_repo:
        just_repo = get_justification_repo(db)
    return EmployeeService(emp_repo, user_repo, att_repo, just_repo)


def get_attendance_service(
    db,
    att_repo=None,
    emp_repo=None,
) -> "AttendanceService":
    from app.services.attendance_service import AttendanceService
    if not att_repo:
        att_repo = get_attendance_repo(db)
    if not emp_repo:
        emp_repo = get_employee_repo(db)
    return AttendanceService(att_repo, emp_repo)


def get_justification_service(
    db,
    just_repo=None,
    emp_repo=None,
) -> "JustificationService":
    from app.services.justification_service import JustificationService
    if not just_repo:
        just_repo = get_justification_repo(db)
    if not emp_repo:
        emp_repo = get_employee_repo(db)
    return JustificationService(just_repo, emp_repo)


def get_visitor_service(
    db,
    vis_repo=None,
) -> "VisitorService":
    from app.services.visitor_service import VisitorService
    if not vis_repo:
        vis_repo = get_visitor_repo(db)
    return VisitorService(vis_repo)