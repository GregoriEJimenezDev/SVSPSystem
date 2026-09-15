import uuid

from sqlalchemy.orm import Session

from app.models.justification import Justification
from app.repositories.justification_repository import JustificationRepository
from app.schemas.justification import JustificationCreate


class JustificationService:
    def __init__(self, db: Session):
        self.repo = JustificationRepository(db)

    def create(self, data: JustificationCreate) -> Justification:
        justification = Justification(**data.model_dump())
        return self.repo.add(justification)

    def list_by_employee(self, employee_id: uuid.UUID) -> list[Justification]:
        return self.repo.list_by_employee(employee_id)
