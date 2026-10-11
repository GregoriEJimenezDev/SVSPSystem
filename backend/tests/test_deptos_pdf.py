"""Tests: departamentos auto-creados por import + ficha PDF de visitante."""

import io

import xlwt
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ADMIN = {
    "email": "pdf-admin@svsp.com",
    "full_name": "Admin PDF",
    "password": "PdfAdmin123!",
    "modules": ["asistencia", "visitas", "adminpro"],
}


def _auth_headers() -> dict:
    client.post("/api/v1/auth/register", json=ADMIN)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN["email"], "password": ADMIN["password"]},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _zkteco_xls_bytes() -> bytes:
    book = xlwt.Workbook()
    sh = book.add_sheet("Exception Statistic Report")
    for c, h in enumerate(["ID", "Name", "Department", "Date", "First time zone", "",
                           "Second time zone", "", "Late"]):
        sh.write(2, c, h)
    for c, h in enumerate(["", "", "", "", "On-duty", "Off-duty", "On-duty", "Off-duty", ""]):
        sh.write(3, c, h)
    rows = [
        ["1", "Pedro Depto", "Depto Nuevo Uno", "2026-10-02", "08:05", "17:02", "", "", ""],
        ["2", "Ana Depto", "Depto Nuevo Dos", "2026-10-02", "07:55", "16:58", "", "", ""],
    ]
    for i, row in enumerate(rows):
        for c, v in enumerate(row):
            sh.write(4 + i, c, v)
    buf = io.BytesIO()
    book.save(buf)
    return buf.getvalue()


def _import(headers) -> dict:
    r = client.post(
        "/api/v1/attendance/import-excel",
        files={"file": ("rep.xls", _zkteco_xls_bytes(), "application/vnd.ms-excel")},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_import_auto_creates_departments():
    h = _auth_headers()
    body = _import(h)
    assert body["departments_created"] >= 2, body
    names = [d["name"] for d in client.get("/api/v1/departments/", headers=h).json()]
    assert "Depto Nuevo Uno" in names
    assert "Depto Nuevo Dos" in names
    # re-importar no duplica departamentos
    body2 = _import(h)
    assert body2["departments_created"] == 0, body2


def test_visitor_pdf_download():
    h = _auth_headers()
    r = client.post("/api/v1/visitors/", json={
        "first_name": "Visita", "last_name": "Pdf",
        "document_number": "001-0101010-1",
        "visited_person": "Director General",
        "institution": "Ministerio de Prueba",
        "visit_justification": "Trámite documental",
    }, headers=h)
    assert r.status_code == 201, r.text
    vid = r.json()["visitor"]["id"]
    r = client.get(f"/api/v1/visitors/{vid}/pdf", headers=h)
    assert r.status_code == 200, r.text[:200]
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
    assert len(r.content) > 2000


def test_visitor_pdf_404():
    h = _auth_headers()
    r = client.get("/api/v1/visitors/999999/pdf", headers=h)
    assert r.status_code == 404, r.text
