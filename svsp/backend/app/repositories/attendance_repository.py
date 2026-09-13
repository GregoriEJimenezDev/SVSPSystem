from datetime import date

from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):
    def __init__(self, db: Session):
        super().__init__(db, Attendance)

    def list_between(self, start: date, end: date) -> list[Attendance]:
        return (
            self.db.query(Attendance)
            .filter(Attendance.work_date >= start, Attendance.work_date <= end)
            .all()
        )

    def delete_older_than(self, cutoff: date) -> int:
        count = self.db.query(Attendance).filter(Attendance.work_date < cutoff).delete()
        self.db.commit()
        return count
