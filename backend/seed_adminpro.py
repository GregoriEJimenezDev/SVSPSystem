"""Script para crear el usuario AdminPRO inicial"""

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import get_settings, Settings
from core.security import hash_password
from core.models import Base, User, Role, ModuleEnum
from core.schemas import UserCreate

# Obtener configuración
settings = get_settings()

# Crear motor de base de datos
engine = create_engine(
    settings.database_url.replace("postgresql://", "postgresql+psycopg2://"),
    pool_pre_ping=True,
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_adminpro_user():
    """Crear el usuario AdminPRO por defecto"""
    db = SessionLocal()
    try:
        # Verificar si ya existe un usuario AdminPRO
        existing = db.query(User).filter(User.email == settings.admin_email).first()

        if existing:
            print(f"⚠️  Usuario AdminPRO ya existe: {settings.admin_email}")
            return

        # Verificar si existe algún usuario con rol AdminPRO
        admin_user = db.query(User).filter(User.modules.contains(["adminpro"])).first()

        if not admin_user:
            # Crear usuario AdminPRO
            user_create = UserCreate(
                email=settings.admin_email,
                full_name=settings.admin_full_name,
                password=settings.admin_password,
                modules=["asistencia", "visitas", "adminpro"],
            )

            # Hashear contraseña
            hashed_pw = hash_password(user_create.password)

            new_user = User(
                email=user_create.email,
                full_name=user_create.full_name,
                hashed_password=hashed_pw,
                modules=user_create.modules,
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            print(f"✅ Usuario AdminPRO creado exitosamente")
            print(f"   Email: {settings.admin_email}")
            print(f"   Nombre: {settings.admin_full_name}")
            print(f"   Módulos: {', '.join(user_create.modules)}")
        else:
            print("ℹ️  Ya existe un usuario con acceso AdminPRO")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear usuario AdminPRO: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Ejecutando seed_adminpro.py...")
    create_adminpro_user()
    print("✅ Finalizado")
