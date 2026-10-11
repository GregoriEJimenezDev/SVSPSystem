"""Tests de coherencia de estadísticas: presentes <= empleados, tardanzas reales."""

from datetime import date, time, timedelta

from fastapi.testclient import TestClient

from app.main import app
from core.database import SessionLocal
from core.models import Attendance, Employee

client = TestClient(app)

ADMIN = {
    "email": "stats-admin@svsp.com",
    "full_name": "Admin Stats",
    "password": "StatsAdmin123!",
    "modules": ["asistencia", "adminpro"],
}

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)


def _auth_headers() -> dict:
    client.post("/api/v1/auth/register", json=ADMIN)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN["email"], "password": ADMIN["password"]},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _seed():
    db = SessionLocal()
    try:
        if db.query(Employee).filter(Employee.name == "Stat Uno").first():
            return
        e1 = Employee(name="Stat Uno", department="StatNorte", is_active=True)
        e2 = Employee(name="Stat Dos", department="StatNorte", is_active=True)
        e3 = Employee(name="Stat Tres", department="StatSur", is_active=True)
        e4 = Employee(name="Stat Cuatro", department="StatNorte", is_active=False)
        db.add_all([e1, e2, e3, e4])
        db.commit()
        for e in (e1, e2, e3, e4):
            db.refresh(e)
        rows = [
            # Hoy: E1 puntual, E2 tarde (+ duplicado mismo día), E3 ausente
            (e1.id, TODAY, time(7, 55), time(17, 0), "9.0"),
            (e2.id, TODAY, time(8, 30), time(17, 5), "8.5"),
            (e2.id, TODAY, time(8, 31), time(17, 6), "8.5"),
            # Ayer: E1 y E3 presentes
            (e1.id, YESTERDAY, time(7, 50), time(17, 0), "9.0"),
            (e3.id, YESTERDAY, time(8, 5), time(17, 0), "8.9"),
        ]
        for emp_id, d, ci, co, th in rows:
            db.add(Attendance(employee_id=emp_id, date=d, check_in=ci,
                              check_out=co, total_hours=th, source="test"))
        db.commit()
    finally:
        db.close()


def test_stats_coherentes_hoy():
    _seed()
    h = _auth_headers()
    s = client.get("/api/v1/attendance/stats", headers=h).json()
    # Solo cuentan E1/E2/E3 (E4 inactivo) en los datos de ESTE test... pero la
    # DB compartida puede tener más empleados de otros tests: invariantes.
    assert s["present_today"] <= s["total_employees"]
    assert s["absent_today"] == s["total_employees"] - s["present_today"]
    assert s["absent_today"] >= 0


def test_stats_duplicados_no_inflan_presentes():
    _seed()
    h = _auth_headers()
    s = client.get(
        f"/api/v1/attendance/stats?start_date={TODAY}&end_date={TODAY}"
        "&department=StatNorte",
        headers=h,
    ).json()
    assert s["total_employees"] == 2, s          # E1, E2 (E4 inactivo fuera)
    assert s["present_today"] == 2, s           # duplicado de E2 cuenta una vez
    assert s["absent_today"] == 0, s
    assert s["late_today"] == 1, s              # E2 entró 08:30 > 08:00


def test_stats_ayer():
    _seed()
    h = _auth_headers()
    s = client.get(
        f"/api/v1/attendance/stats?start_date={YESTERDAY}&end_date={YESTERDAY}",
        headers=h,
        params={},
    ).json()
    assert s["present_today"] == 2, s           # E1 y E3
    assert s["late_today"] == 1, s              # E3 entró 08:05


def test_chart_data_coherente():
    _seed()
    h = _auth_headers()
    c = client.get("/api/v1/attendance/chart-data", headers=h).json()
    assert c["present"] <= c["present"] + c["absent"]
    assert c["absent"] >= 0
    assert c["late"] >= 0
