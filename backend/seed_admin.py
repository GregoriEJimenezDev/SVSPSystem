"""Create tables and seed the default admin user."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from passlib.context import CryptContext

from app.config import settings
from app.models import Base, User

ADMIN_EMAIL = "admin@svsp.com"
ADMIN_PASSWORD = "admin123"

connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)
engine = create_engine(settings.database_url, connect_args=connect_args)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
try:
    existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if existing:
        print(f"Admin already exists: {existing.email} (id={existing.id})")
    else:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user = User(
            email=ADMIN_EMAIL,
            full_name="Administrador",
            password_hash=pwd_context.hash(ADMIN_PASSWORD),
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Admin created: {user.email} (id={user.id})")
finally:
    db.close()
