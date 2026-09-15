import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_adminpro
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.user_service import EmailAlreadyExistsError, UserService

router = APIRouter(prefix="/api/users", tags=["Usuarios (AdminPRO)"], dependencies=[Depends(require_adminpro)])


@router.post("/", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return UserService(db).create_user(payload)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return UserService(db).list_users()


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: uuid.UUID, payload: UserUpdate, db: Session = Depends(get_db)):
    return UserService(db).update_user(user_id, payload)
