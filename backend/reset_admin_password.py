"""Restablece la contrasena de un usuario existente.

Uso (en el Codespace, dentro de backend/):
    python reset_admin_password.py admin@svsp.local 'NuevaClave123!'

Lee la conexion desde backend/.env (DATABASE_URL). No imprime la clave.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=Path(__file__).parent / ".env")
except ImportError:
    pass

from core.security import hash_password, verify_password
from core.database import SessionLocal
from core.models import User


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: python reset_admin_password.py <email> <nueva-clave>")
        return 2
    email, new_password = sys.argv[1], sys.argv[2]
    if len(new_password) < 8:
        print("ERROR: la clave debe tener al menos 8 caracteres.")
        return 2

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"ERROR: no existe el usuario {email}")
            return 1
        user.password_hash = hash_password(new_password)
        user.is_active = True
        db.commit()
        ok = verify_password(
            new_password,
            db.query(User).filter(User.email == email).first().password_hash,
        )
        print(f"OK: clave actualizada para {email} (verificada={ok})")
        return 0 if ok else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
