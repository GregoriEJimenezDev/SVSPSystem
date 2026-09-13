from sqlalchemy.orm import Session

from app.models.justification import Justification
from app.repositories.base import BaseRepository


class JustificationRepository(BaseRepository[Justification]):
    def __init__(self, db: Session):
        super().__init__(db, Justification)

    def list_by_employee(self, employee_id) -> list[Justification]:
        return self.db.query(Justification).filter(Justification.employee_id == employee_id).all()
