from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.models import User, Employee, Attendance, Justification, Visitor, Role, Permission


# Helper to import schemas locally to avoid circular imports
def _import_schemas():
    from app.schemas import (
        EmployeeCreate,
        EmployeeUpdate,
        EmployeeResponse,
        AttendanceCreate,
        AttendanceResponse,
        JustificationCreate,
        JustificationUpdate,
        JustificationResponse,
        VisitorCreate,
        VisitorUpdate,
        VisitorResponse,
        Token,
        TokenData,
    )
    return (
        EmployeeCreate,
        EmployeeUpdate,
        EmployeeResponse,
        AttendanceCreate,
        AttendanceResponse,
        JustificationCreate,
        JustificationUpdate,
        JustificationResponse,
        VisitorCreate,
        VisitorUpdate,
        VisitorResponse,
        Token,
        TokenData,
    )


# -- User Repository --
class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, data: dict) -> User:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(data.get("password", ""))
        db_obj = User(
            email=data.get("email", ""),
            full_name=data.get("full_name", ""),
            password_hash=hashed_password,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: User, data: dict) -> User:
        for key, value in data.items():
            setattr(db_obj, key, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def soft_delete(self, db_obj: User) -> User:
        db_obj.is_active = False
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj