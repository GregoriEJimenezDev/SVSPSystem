from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import get_settings

from app.routers import auth, employees, attendance, visitors, justifications, adminpro

from core.config import get_settings

settings = get_settings()

_UNCONFIGURED_DB_URL = "postgresql://user:password@localhost:5432/svsp"
_UNCONFIGURED_SECRET = "change-me-in-production-min-32-chars"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Falla rapido con mensaje claro si falta configuracion esencial."""
    if settings.database_url == _UNCONFIGURED_DB_URL:
        raise RuntimeError(
            "DATABASE_URL no configurado. Crea backend/.env con tu conexion "
            "(ver backend/.env.example). La app se niega a arrancar sin base de datos."
        )
    if not settings.secret_key or settings.secret_key == _UNCONFIGURED_SECRET:
        raise RuntimeError(
            "SECRET_KEY no configurado o es el valor de ejemplo. Define uno propio "
            "de al menos 32 caracteres en backend/.env (ver backend/.env.example)."
        )
    if len(settings.secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY demasiado corto (minimo 32 caracteres). "
            "Genera uno con: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="SVSP - Sistema Web de Gestión de Asistencia y Visitas",
    lifespan=lifespan,
)

# CORS configurado explícitamente con orígenes desde settings.
# allow_origin_regex cubre los frontends servidos desde GitHub Codespaces
# (*.app.github.dev), donde el navegador no puede usar localhost.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.app\.github\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers (cada router ya trae su prefijo /api/v1/...)
app.include_router(auth.router, tags=["Autenticación"])
app.include_router(employees.router, tags=["Empleados"])
app.include_router(attendance.router, tags=["Asistencia"])
app.include_router(visitors.router, tags=["Visitas"])
app.include_router(justifications.router, tags=["Justificaciones"])
app.include_router(adminpro.router, tags=["AdminPRO"])


# Ruta raíz
@app.get("/")
def root():
    return {
        "message": "SVSP API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Ruta de salud
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "svsp-backend"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
