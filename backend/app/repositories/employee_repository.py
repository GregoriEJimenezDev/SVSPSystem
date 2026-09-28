from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.models import User, Employee, Attendance, Justification, Visitor, Role, Permission


class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user(self, user_id: int) -> Optional[Employee]:
        return self.db.query(Employee).filter(Employee.user_id == user_id).first()

    def get_by_id(self, employee_id: int) -> Optional[Employee]:
        return self.db.query(Employee).filter(Employee.id == employee_id).first()

    def get_all_active(self) -> List[Employee]:
        return self.db.query(Employee).filter(Employee.is_active == True).all()

    def get_by_department(self, department: str) -> List[Employee]:
        return (
            self.db.query(Employee)
            .filter(Employee.department == department, Employee.is_active == True)
            .all()
        )

    def create_with_user(self, user_id: int, name: str, department: Optional[str] = None) -> Employee:
        emp = Employee(user_id=user_id, name=name, department=department)
        self.db.add(emp)
        self.db.commit()
        self.db.refresh(emp)
        return emp

    def update(self, db_obj: Employee, data: dict) -> Employee:
        if "name" in data:
            db_obj.name = data["name"]
        if "department" in data:
            db_obj.department = data["department"]
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def soft_delete(self, db_obj: Employee) -> Employee:
        db_obj.is_active = False
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj