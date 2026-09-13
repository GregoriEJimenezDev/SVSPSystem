from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import (
    create_access_token,
    decode_token,
    verify_password,
    hash_password,
)
from core.schemas import UserCreate, UserResponse, Token
from core.models import User
from core.dependencies import log_audit

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate, db: Session = Depends(get_db), request: Request = None
):
    """Registrar un nuevo usuario"""
    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado",
        )

    # Hashear contraseña
    hashed_pw = hash_password(user_data.password)

    # Crear usuario
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
        modules=user_data.modules or [],
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log de auditoría
    log_audit(
        db=db,
        user_id=None,  # System user
        action="create_user",
        entity_type="user",
        entity_id=new_user.id,
        details={"email": new_user.email, "modules": new_user.modules},
        request=request,
    )

    # Generar token
    access_token = create_access_token(
        data={"sub": new_user.email},
        expires_delta=None,  # Will use default from settings
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(email: str, password: str, db: Session = Depends(get_db)):
    """Iniciar sesión"""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email},
    )

    return {"access_token": access_token, "token_type": "bearer"}
