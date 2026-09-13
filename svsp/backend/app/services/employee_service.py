import uuid

from sqlalchemy.orm import Session

from app.models.employee import Employee, EmployeeStatus
from app.repositories.employee_repository import EmployeeRepository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    """Reglas de negocio de empleados. Regla clave: nunca se elimina un
    empleado, solo se inhabilita o rehabilita.
    """

    def __init__(self, db: Session):
        self.repo = EmployeeRepository(db)

    def create(self, data: EmployeeCreate) -> Employee:
        employee = Employee(full_name=data.full_name, department=data.department)
        return self.repo.add(employee)

    def get_or_create_by_name(self, full_name: str, department: str = "Sin asignar") -> tuple[Employee, bool]:
        employee = self.repo.get_by_full_name(full_name)
        if employee:
            return employee, False
        employee = Employee(full_name=full_name, department=department)
        return self.repo.add(employee), True

    def list(self) -> list[Employee]:
        return self.repo.list()

    def update(self, employee_id: uuid.UUID, data: EmployeeUpdate) -> Employee | None:
        employee = self.repo.get(employee_id)
        if not employee:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(employee, field, value)
        return self.repo.save(employee)

    def set_status(self, employee_id: uuid.UUID, status: EmployeeStatus) -> Employee | None:
        employee = self.repo.get(employee_id)
        if not employee:
            return None
        employee.status = status
        return self.repo.save(employee)
