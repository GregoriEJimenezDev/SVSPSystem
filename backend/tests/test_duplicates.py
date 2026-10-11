"""Tests de normalizacion de nombres, deteccion y fusion de duplicados."""

from datetime import date, time

from fastapi.testclient import TestClient

from app.main import app
from core.database import SessionLocal
from core.models import Attendance, Employee

client = TestClient(app)

ADMIN = {
    "email": "dedup-admin@svsp.com",
    "full_name": "Admin Dedup",
    "password": "DedupAdmin123!",
    "modules": ["asistencia", "adminpro"],
}


def _auth_headers() -> dict:
    client.post("/api/v1/auth/register", json=ADMIN)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN["email"], "password": ADMIN["password"]},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _seed_dupes():
    db = SessionLocal()
    try:
        a = db.query(Employee).filter(Employee.name == "Dup Uno").first()
        if a:
            b = db.query(Employee).filter(Employee.name == "Dup  Uno").first()
            c = db.query(Employee).filter(Employee.name == "dup uno").first()
            d = db.query(Employee).filter(Employee.name == "Unico Solo").first()
            return {"a": a.id, "b": b.id, "c": c.id, "d": d.id}
        a = Employee(name="Dup Uno", department="X", is_active=True)
        b = Employee(name="Dup  Uno", department="X", is_active=True)  # doble espacio
        c = Employee(name="dup uno", department="Y", is_active=True)  # otra capitalización
        d = Employee(name="Unico Solo", department="X", is_active=True)
        db.add_all([a, b, c, d])
        db.commit()
        for e in (a, b, c, d):
            db.refresh(e)
        db.add(Attendance(employee_id=b.id, date=date(2026, 10, 2),
                          check_in=time(8, 0), check_out=time(17, 0), total_hours="9.0"))
        db.commit()
        return {"a": a.id, "b": b.id, "c": c.id, "d": d.id}
    finally:
        db.close()


def test_duplicates_detected():
    _seed_dupes()
    h = _auth_headers()
    groups = client.get("/api/v1/employees/duplicates", headers=h).json()
    keys = [g["key"] for g in groups]
    assert "dup uno" in keys
    dup = next(g for g in groups if g["key"] == "dup uno")
    assert len(dup["employees"]) == 3
    assert not any(g["key"] == "unico solo" for g in groups)


def test_merge_moves_records_and_deactivates():
    ids = _seed_dupes()
    h = _auth_headers()
    # el POST normaliza el nombre (strip + espacios simples)
    r = client.post("/api/v1/employees/", json={"name": "Dup   Uno", "department": "X"}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "Dup Uno"
    # la fusión mueve la asistencia de b->a y desactiva b y c
    r = client.post("/api/v1/employees/merge",
                    json={"keep_id": ids["a"], "duplicate_ids": [ids["b"], ids["c"]]},
                    headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["keep_id"] == ids["a"]
    assert sorted(body["deactivated_ids"]) == sorted([ids["b"], ids["c"]])
    assert body["moved_attendances"] >= 1
    db = SessionLocal()
    try:
        assert db.query(Attendance).filter(Attendance.employee_id == ids["b"]).count() == 0
        assert db.query(Employee).filter(Employee.id == ids["b"]).first().is_active is False
        assert db.query(Employee).filter(Employee.id == ids["a"]).first().is_active is True
    finally:
        db.close()


def test_merge_validations():
    _seed_dupes()
    h = _auth_headers()
    # sin duplicados
    r = client.post("/api/v1/employees/merge", json={"keep_id": 1, "duplicate_ids": []}, headers=h)
    assert r.status_code == 422, r.text  # min_length=1 del schema
    # conservado inexistente
    r = client.post("/api/v1/employees/merge", json={"keep_id": 999999, "duplicate_ids": [1]}, headers=h)
    assert r.status_code == 404, r.text


def test_create_normalizes_name():
    h = _auth_headers()
    r = client.post("/api/v1/employees/",
                    json={"name": "  Espaciado   Raro  ", "department": "X"}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "Espaciado Raro"
