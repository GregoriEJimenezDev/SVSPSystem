from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.models import Attendance


class AttendanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> Attendance:
        from datetime import datetime
        db_obj = Attendance(
            employee_id=data.get("employee_id"),
            check_in=datetime.utcnow(),
            check_out=None,
            total_hours="00:00",
            date=datetime.utcnow(),
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_employee(
        self, employee_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Attendance]:
        from sqlalchemy import and_
        query = self.db.query(Attendance).filter(Attendance.employee_id == employee_id)
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        return query.order_by(Attendance.date.desc()).all()

    def get_recent(self, limit: int = 50) -> List[Attendance]:
        return (
            self.db.query(Attendance)
            .order_by(Attendance.date.desc())
            .limit(limit)
            .all()
        )