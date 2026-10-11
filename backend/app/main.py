from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings

from app.routers import auth, employees, attendance, visitors, justifications, adminpro

from core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="SVSP - Sistema Web de Gestión de Asistencia y Visitas",
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
