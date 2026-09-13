from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    def __init__(self, db: Session):
        super().__init__(db, Employee)

    def get_by_full_name(self, full_name: str) -> Employee | None:
        return self.db.query(Employee).filter(Employee.full_name == full_name).first()
