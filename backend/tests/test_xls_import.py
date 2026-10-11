"""Tests de importacion Excel (.xls ZKTeco y .xlsx simple)."""

import io

import xlwt
from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app

client = TestClient(app)

ADMIN = {
    "email": "xls-admin@svsp.com",
    "full_name": "Admin XLS",
    "password": "XlsAdmin123!",
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


def _zkteco_xls_bytes() -> bytes:
    """Mini-reporte estilo ZKTeco StandardReport (Exception Statistic Report)."""
    book = xlwt.Workbook()
    sh = book.add_sheet("Exception Statistic Report")
    headers = ["ID", "Name", "Department", "Date", "First time zone", "",
               "Second time zone", "", "Late time(Min)"]
    sub = ["", "", "", "", "On-duty", "Off-duty", "On-duty", "Off-duty", ""]
    rows = [
        ["1", "Ana Prueba", "TECNOLOGIA", "2026-10-02", "08:05", "17:02", "", "", "5.0"],
        ["2", "Luis Prueba", "COCINA", "2026-10-02", "07:55", "16:58", "", "", "0.0"],
    ]
    for c, h in enumerate(headers):
        sh.write(2, c, h)
    for c, h in enumerate(sub):
        sh.write(3, c, h)
    for i, row in enumerate(rows):
        for c, v in enumerate(row):
            sh.write(4 + i, c, v)
    buf = io.BytesIO()
    book.save(buf)
    return buf.getvalue()


def _simple_xlsx_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(["empleado", "hora_entrada", "hora_salida"])
    ws.append(["Carlos Simple", "08:00", "17:00"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_import_zkteco_xls():
    h = _auth_headers()
    r = client.post(
        "/api/v1/attendance/import-excel",
        files={"file": ("reporte.xls", _zkteco_xls_bytes(), "application/vnd.ms-excel")},
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["processed"] == 2, body
    assert body["created"] == 2, body
    assert body["errors"] == []


def test_import_simple_xlsx_still_works():
    h = _auth_headers()
    r = client.post(
        "/api/v1/attendance/import-excel",
        files={"file": ("planilla.xlsx", _simple_xlsx_bytes(),
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["processed"] == 1


def test_import_invalid_file_400():
    h = _auth_headers()
    r = client.post(
        "/api/v1/attendance/import-excel",
        files={"file": ("notas.txt", b"esto no es excel", "text/plain")},
        headers=h,
    )
    assert r.status_code == 400, r.text
    assert ".xls" in r.json()["detail"]


def test_import_zkteco_records_land_on_report_date():
    h = _auth_headers()
    client.post(
        "/api/v1/attendance/import-excel",
        files={"file": ("reporte.xls", _zkteco_xls_bytes(), "application/vnd.ms-excel")},
        headers=h,
    )
    r = client.get("/api/v1/attendance/", headers=h)
    assert r.status_code == 200, r.text
    fechas = {a["date"][:10] for a in r.json()}
    assert "2026-10-02" in fechas
