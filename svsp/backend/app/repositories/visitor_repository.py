from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.visitor import Visitor
from app.repositories.base import BaseRepository


class VisitorRepository(BaseRepository[Visitor]):
    def __init__(self, db: Session):
        super().__init__(db, Visitor)

    def search(self, term: str) -> list[Visitor]:
        like = f"%{term}%"
        return (
            self.db.query(Visitor)
            .filter(
                or_(
                    Visitor.cedula.ilike(like),
                    Visitor.first_name.ilike(like),
                    Visitor.last_name.ilike(like),
                )
            )
            .all()
        )
