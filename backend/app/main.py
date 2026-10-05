from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SVSP - Sistema de Visitas y Asistencia",
    description="Sistema integrado con módulos de Asistencia, Visitas y AdminPRO",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS - allow Codespaces frontend, local Vite, and production deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers individually to avoid module state conflicts
from app.routers.auth_router import router as auth_router
app.include_router(auth_router, prefix="/api")

from app.routers.employee_router import router as employee_router
app.include_router(employee_router, prefix="/api")

from app.routers.attendance_router import router as attendance_router
app.include_router(attendance_router, prefix="/api")

from app.routers.justification_router import router as justification_router
app.include_router(justification_router, prefix="/api")

from app.routers.visitor_router import router as visitor_router
app.include_router(visitor_router, prefix="/api")

from app.routers.user_router import router as user_router
app.include_router(user_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "SVSP API - Bienvenido al sistema de Visitas y Asistencia"}