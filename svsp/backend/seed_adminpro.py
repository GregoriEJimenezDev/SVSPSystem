"""Script para crear el primer usuario AdminPRO.
Uso: python seed_adminpro.py
"""
import getpass

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.user import User, UserRole


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        email = input("Correo del AdminPRO: ").strip()
        full_name = input("Nombre completo: ").strip()
        password = getpass.getpass("Contrasena: ")

        if db.query(User).filter(User.email == email).first():
            print("Ya existe un usuario con ese correo.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.ADMINPRO,
            modules=["asistencia", "visitas"],
        )
        db.add(admin)
        db.commit()
        print(f"Usuario AdminPRO '{email}' creado correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
