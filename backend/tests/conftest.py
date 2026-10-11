"""Pytest bootstrap: SQLite temporal ANTES de importar la app.

La app en produccion usa Neon (PostgreSQL). Los tests usan SQLite en un
archivo temporal para no tocar ningun dato real y correr sin credenciales.
"""

import os
import sys
import tempfile

_TMPDIR = tempfile.mkdtemp(prefix="svsp-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMPDIR}/test.db"
os.environ.setdefault("SECRET_KEY", "x" * 40)

# backend/ debe estar en sys.path para `import app...` / `import core...`
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from core.config import get_settings

get_settings.cache_clear()

import core.models  # noqa: F401  (registra los modelos en Base)
from core.database import Base, engine  # noqa: E402

Base.metadata.create_all(bind=engine)
