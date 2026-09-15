from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import SessionLocal
from app.routers import attendance, auth, employees, justifications, users, visitors
from app.services.attendance_service import AttendanceService

scheduler = BackgroundScheduler()


def purge_old_attendance_job():
    db = SessionLocal()
    try:
        deleted = AttendanceService(db).purge_old_reports(settings.attendance_retention_days)
        if deleted:
            print(f"[scheduler] Reportes de asistencia eliminados por retencion: {deleted}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ejecuta la purga de reportes vencidos una vez al dia.
    scheduler.add_job(purge_old_attendance_job, "interval", days=1, id="purge_attendance")
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="SVSP - Sistema de Asistencia y Visitas", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(justifications.router)
app.include_router(visitors.router)
app.include_router(users.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
