"""Tests del flujo de autenticacion: register / login.

- 201 al registrar + devuelve access_token y usuario
- 400 al duplicar email
- 200 al login correcto + devuelve access_token
- 401 + "Credenciales incorrectas" con clave mala o usuario inexistente
- 422 con password demasiado corta en register (minimo 8)
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ADMIN = {"email": "ci-admin@svsp.com", "full_name": "CI Admin", "password": "CiAdmin123!"}


def test_root_ok():
    r = client.get("/")
    assert r.status_code == 200


def test_register_ok():
    r = client.post("/api/v1/auth/register", json=ADMIN)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == ADMIN["email"]


def test_register_duplicate_400():
    client.post("/api/v1/auth/register", json=ADMIN)
    r = client.post("/api/v1/auth/register", json=ADMIN)
    assert r.status_code == 400, r.text


def test_register_short_password_422():
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "corto@svsp.com", "full_name": "Corto", "password": "abc"},
    )
    assert r.status_code == 422, r.text


def test_login_ok():
    client.post("/api/v1/auth/register", json=ADMIN)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN["email"], "password": ADMIN["password"]},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"]
    assert body["user"]["email"] == ADMIN["email"]


def test_login_wrong_password_401():
    client.post("/api/v1/auth/register", json=ADMIN)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN["email"], "password": "clave-mala-123"},
    )
    assert r.status_code == 401, r.text
    assert r.json()["detail"] == "Credenciales incorrectas"


def test_login_unknown_user_401():
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "nadie@svsp.com", "password": "cualquier123"},
    )
    assert r.status_code == 401, r.text
