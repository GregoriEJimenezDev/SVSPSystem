from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.models import Justification


class JustificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> Justification:
        db_obj = Justification(
            employee_id=data.get("employee_id"),
            type=data.get("type"),
            description=data.get("description"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_employee(
        self, employee_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Justification]:
        query = self.db.query(Justification).filter(Justification.employee_id == employee_id)
        if start_date:
            query = query.filter(Justification.start_date >= start_date)
        if end_date:
            query = query.filter(Justification.end_date <= end_date)
        return query.order_by(Justification.created_at.desc()).all()

    def get_all_active(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Justification]:
        query = self.db.query(Justification)
        if start_date:
            query = query.filter(Justification.start_date >= start_date)
        if end_date:
            query = query.filter(Justification.end_date <= end_date)
        return query.order_by(Justification.created_at.desc()).all()