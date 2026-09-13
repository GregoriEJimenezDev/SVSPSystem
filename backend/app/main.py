from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="SVSP - Sistema Web de Gestión de Asistencia y Visitas",
)

# CORS configurado explícitamente con orígenes desde settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers de la API v1
app.include_router(auth.router, prefix="/api/v1", tags=["Autenticación"])
app.include_router(employees.router, prefix="/api/v1", tags=["Empleados"])
app.include_router(attendance.router, prefix="/api/v1", tags=["Asistencia"])
app.include_router(visitors.router, prefix="/api/v1", tags=["Visitas"])
app.include_router(justifications.router, prefix="/api/v1", tags=["Justificaciones"])
app.include_router(adminpro.router, prefix="/api/v1", tags=["AdminPRO"])


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
