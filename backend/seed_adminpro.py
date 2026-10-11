"""Script para crear el usuario AdminPRO inicial.

Uso:
    set DATABASE_URL=postgresql://...   (Windows CMD)
    $env:DATABASE_URL="postgresql://..."  (PowerShell)
    export DATABASE_URL="postgresql://..." (Linux/macOS)
    python seed_adminpro.py

    Opcional (defaults entre paréntesis):
    ADMIN_EMAIL (admin@svsp.local)
    ADMIN_PASSWORD (Admin123!)
    ADMIN_FULL_NAME (Administrador SVSP)

NUNCA hardcodees credenciales reales en este archivo: quedan en el historial de git.
"""

import os
import sys

if not os.getenv("DATABASE_URL"):
    print(
        "ERROR: define la variable de entorno DATABASE_URL antes de ejecutar.\n"
        'Ejemplo (PowerShell): $env:DATABASE_URL="postgresql://usuario:clave@host:5432/svsp"'
    )
    sys.exit(1)

from core.config import get_settings
from core.security import hash_password
from core.database import engine, Base, SessionLocal
from core.models import User


def create_adminpro_user():
    """Crear el usuario AdminPRO por defecto (credenciales por variables de entorno)"""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@svsp.local")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!")
    admin_full_name = os.getenv("ADMIN_FULL_NAME", "Administrador SVSP")

    db = SessionLocal()
    try:
        # Verificar si ya existe un usuario AdminPRO
        existing = db.query(User).filter(User.email == admin_email).first()

        if existing:
            print(f"Usuario AdminPRO ya existe: {existing.email}")
            return

        # Crear usuario AdminPRO
        hashed_pw = hash_password(admin_password)

        new_user = User(
            email=admin_email,
            full_name=admin_full_name,
            hashed_password=hashed_pw,
            modules=["asistencia", "visitas", "adminpro"],
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print("Usuario AdminPRO creado exitosamente")
        print(f"Email: {new_user.email}")
        print(f"Nombre: {new_user.full_name}")
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
