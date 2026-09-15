import uuid
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Repositorio generico: encapsula el acceso a datos para un modelo,
    manteniendo a los servicios independientes de SQLAlchemy (principio
    de inversion de dependencias).
    """

    def __init__(self, db: Session, model: type[ModelType]):
        self.db = db
        self.model = model

    def get(self, id_: uuid.UUID) -> ModelType | None:
        return self.db.get(self.model, id_)

    def list(self) -> list[ModelType]:
        return self.db.query(self.model).all()

    def add(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def save(self, obj: ModelType) -> ModelType:
        self.db.commit()
        self.db.refresh(obj)
        return obj
