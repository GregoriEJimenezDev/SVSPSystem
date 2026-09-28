from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.models import Visitor


class VisitorRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> Visitor:
        db_obj = Visitor(
            name=data.get("name"),
            last_name=data.get("last_name"),
            cedula=data.get("cedula"),
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_cedula(self, cedula: str) -> Optional[Visitor]:
        return self.db.query(Visitor).filter(Visitor.cedula == cedula).first()

    def get_all_active(self) -> List[Visitor]:
        return self.db.query(Visitor).filter(Visitor.is_active == True).all()

    def get_by_name(self, name: str) -> List[Visitor]:
        return (
            self.db.query(Visitor)
            .filter(Visitor.name.ilike(f"%{name}%"), Visitor.is_active == True)
            .all()
        )

    def soft_delete(self, db_obj: Visitor) -> Visitor:
        db_obj.is_active = False
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj