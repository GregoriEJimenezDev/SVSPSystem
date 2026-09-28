from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User
from passlib.context import CryptContext
from jose import JWTError, jwt


def get_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency: Current active user (with JWT)
def get_current_active_user(
    db: Session = Depends(get_db),
):
    # In production, decode JWT token from Authorization header
    # For now, return a user by email for development
    user = db.query(User).filter(User.email == "admin@svsp.local").first()
    if not user:
        # Create a default user if none exists
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash("admin123")
        user = User(
            email="admin@svsp.local",
            full_name="Administrador",
            password_hash=hashed,
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User inactive")
    return user


# Dependency: Current active user with module access
def get_current_active_user_with_module_access(
    modulo: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Validate user has access to the requested module
    if current_user.is_superuser:
        return current_user
    
    module_access = getattr(current_user, "module_access", None) if hasattr(current_user, "module_access") else None
    
    if modulo == "ambos":
        return current_user
    elif modulo and module_access:
        if module_access not in [modulo, "ambos"]:
            raise HTTPException(
                status_code=403,
                detail=f"Usuario sin acceso al módulo '{modulo}'",
            )
    return current_user


# Dependency: Superuser only
def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos de administrador",
        )
    return current_user