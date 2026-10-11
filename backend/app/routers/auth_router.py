from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
from app.dependencies import get_db
from app.schemas import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
)
from app.services.auth_service import get_auth_service
from app.dependencies import get_current_active_user, get_current_superuser
from app.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    auth = get_auth_service(db)
    # Check if user already exists
    existing = auth.db.get_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return auth.create(user)


@router.post("/login", response_model=Token)
def login(form_data: UserLogin, db: Session = Depends(get_db)):
    auth = get_auth_service(db)
    user = auth.authenticate(form_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    access_token = auth.create_access_token(sub=user.email)
    refresh_token = auth.create_access_token(sub=f"refresh:{user.email}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_active_user)):
    return current_user