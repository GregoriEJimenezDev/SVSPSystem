from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)
from app.services.auth_service import get_auth_service
from app.services import get_employee_service
from app.dependencies import (
    get_current_active_user,
    get_current_superuser,
    get_current_active_user_with_module_access,
)
from app.models import User

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(get_current_superuser)])


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
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
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/{user_id}/role", response_model=UserResponse)
def assign_role(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    # Admin can assign roles to other users
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    from app.models import Role
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    user.role_id = role.id
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}/modules", response_model=UserResponse)
def assign_modules(
    user_id: int,
    modulo_acceso: str,  # "asistencia", "visitas", "ambos"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Assign module access by updating role permissions or a separate flag
    # For now, we'll store it as a simple string on the user
    user.module_access = modulo_acceso
    db.commit()
    db.refresh(user)
    return user