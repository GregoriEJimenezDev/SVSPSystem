"""Script para crear el usuario AdminPRO inicial"""

import os

os.environ["DATABASE_URL"] = (
    "postgresql://neondb_owner:npg_Dznhti7MlLG9@ep-frosty-bar-axkj1odf-pooler.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

from core.config import get_settings
from core.security import hash_password
from core.database import engine, Base, SessionLocal
from core.models import User


def create_adminpro_user():
    """Crear el usuario AdminPRO por defecto"""
    db = SessionLocal()
    try:
        # Verificar si ya existe un usuario AdminPRO
        existing = db.query(User).filter(User.email == "admin@svsp.local").first()

        if existing:
            print("Usuario AdminPRO ya existe: admin@svsp.local")
            return

        # Crear usuario AdminPRO
        hashed_pw = hash_password("Admin123!")

        new_user = User(
            email="admin@svsp.local",
            full_name="Administrador SVSP",
            hashed_password=hashed_pw,
            modules=["asistencia", "visitas", "adminpro"],
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print("Usuario AdminPRO creado exitosamente")
        print("Email: admin@svsp.local")
        print("Nombre: Administrador SVSP")
        print("Modulos: asistencia, visitas, adminpro")

    except Exception as e:
        db.rollback()
        print(f"Error al crear usuario AdminPRO: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Ejecutando seed_adminpro.py...")
    create_adminpro_user()
    print("Finalizado")
