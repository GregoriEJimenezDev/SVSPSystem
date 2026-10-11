"""Aplica las migraciones SQL de backend/migrations/ en orden.

Uso (desde backend/, con backend/.env configurado):
    python apply_migrations.py

Lee DATABASE_URL del entorno o de backend/.env. Los .sql deben ser
idempotentes (IF NOT EXISTS) para poder correrse varias veces.
JAMÁS pongas credenciales en este archivo ni en los .sql.
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent

sys.path.insert(0, str(HERE))

try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=HERE / ".env")
except ImportError:
    pass

import os

from sqlalchemy import create_engine, text


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("ERROR: define DATABASE_URL en backend/.env antes de migrar.")
        return 2

    migrations_dir = HERE / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("No hay migraciones en backend/migrations/.")
        return 0

    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        for path in files:
            # Quita comentarios de línea ANTES de partir (un ';' dentro de un
            # comentario no debe crear sentencias fantasmas).
            code_lines = [
                ln
                for ln in path.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.strip().startswith("--")
            ]
            statements = [
                s.strip() for s in "\n".join(code_lines).split(";") if s.strip()
            ]
            for stmt in statements:
                conn.execute(text(stmt))
            conn.commit()
            print(f"OK: {path.name} ({len(statements)} sentencias)")
    print("Migraciones aplicadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
