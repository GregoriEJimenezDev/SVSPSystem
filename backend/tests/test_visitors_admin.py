"""Tests del modulo Visitas (campos nuevos) y cambio de clave por AdminPRO."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ADMIN = {
    "email": "visitas-admin@svsp.com",
    "full_name": "Admin Visitas",
    "password": "VisitasAdmin123!",
    "modules": ["visitas", "adminpro"],
}
OPERADOR = {
    "email": "visitas-oper@svsp.com",
    "full_name": "Operador Visitas",
    "password": "VisitasOper123!",
    "modules": ["visitas"],
}
VISITA = {
    "first_name": "Juan",
    "last_name": "Pérez",
    "document_number": "402-0000000-1",
    "visited_person": "María Gómez",
    "institution": "Instituto Tecnológico",
    "visit_justification": "Reunión de coordinación académica",
}


def _auth_headers(email: str, password: str) -> dict:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _register(payload: dict) -> dict:
    """Registra (idempotente entre tests: la DB SQLite se comparte en la sesión)."""
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code in (201, 400), r.text
    if r.status_code == 201:
        return r.json()
    # Ya existía: devuelve forma equivalente vía login
    login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200, login.text
    return login.json()


def test_register_visitor_with_new_fields():
    _register(ADMIN)
    h = _auth_headers(ADMIN["email"], ADMIN["password"])
    r = client.post("/api/v1/visitors/", json=VISITA, headers=h)
    assert r.status_code == 201, r.text
    v = r.json()["visitor"]
    assert v["visited_person"] == "María Gómez"
    assert v["institution"] == "Instituto Tecnológico"
    assert v["visit_justification"] == "Reunión de coordinación académica"


def test_get_visitor_includes_new_fields():
    _register(ADMIN)
    h = _auth_headers(ADMIN["email"], ADMIN["password"])
    vid = client.post("/api/v1/visitors/", json=VISITA, headers=h).json()["visitor"]["id"]
    r = client.get(f"/api/v1/visitors/{vid}", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["visited_person"] == "María Gómez"


def test_reregister_same_document_updates_visit_info():
    _register(ADMIN)
    h = _auth_headers(ADMIN["email"], ADMIN["password"])
    client.post("/api/v1/visitors/", json=VISITA, headers=h)
    r = client.post(
        "/api/v1/visitors/",
        json={**VISITA, "visited_person": "Pedro Ruiz", "institution": "Otra Institución"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    v = r.json()["visitor"]
    assert v["visited_person"] == "Pedro Ruiz"
    assert v["institution"] == "Otra Institución"


def test_public_card_shows_visit_info_without_login():
    _register(ADMIN)
    h = _auth_headers(ADMIN["email"], ADMIN["password"])
    vid = client.post("/api/v1/visitors/", json=VISITA, headers=h).json()["visitor"]["id"]
    r = client.get(f"/api/v1/visitors/public/{vid}")
    assert r.status_code == 200, r.text
    assert "María Gómez" in r.text
    assert "Instituto Tecnol" in r.text


def test_adminpro_can_change_user_password():
    admin = _register(ADMIN)
    target = _register(OPERADOR)
    h = _auth_headers(ADMIN["email"], ADMIN["password"])
    r = client.put(
        f"/api/v1/adminpro/users/{target['user']['id']}/password",
        json={"new_password": "NuevaClave123!"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # La respuesta JAMÁS debe exponer la clave ni su hash
    assert "hashed_password" not in body
    assert "new_password" not in body
    assert "password" not in body
    # Login con la nueva funciona, con la vieja falla
    ok = client.post(
        "/api/v1/auth/login",
        json={"email": OPERADOR["email"], "password": "NuevaClave123!"},
    )
    assert ok.status_code == 200, ok.text
    bad = client.post(
        "/api/v1/auth/login",
        json={"email": OPERADOR["email"], "password": OPERADOR["password"]},
    )
    assert bad.status_code == 401


def test_non_admin_cannot_change_passwords():
    _register(ADMIN)
    solo_visitas = {
        "email": "solo-visitas@svsp.com",
        "full_name": "Solo Visitas",
        "password": "SoloVisitas123!",
        "modules": ["visitas"],
    }
    target = _register(solo_visitas)
    h = _auth_headers(solo_visitas["email"], solo_visitas["password"])
    r = client.put(
        f"/api/v1/adminpro/users/{target['user']['id']}/password",
        json={"new_password": "OtraClave123!"},
        headers=h,
    )
    assert r.status_code == 403, r.text


def test_change_password_unknown_user_404():
    _register(ADMIN)
    h = _auth_headers(ADMIN["email"], ADMIN["password"])
    r = client.put(
        "/api/v1/adminpro/users/999999/password",
        json={"new_password": "OtraClave123!"},
        headers=h,
    )
    assert r.status_code == 404, r.text


def test_change_password_too_short_422():
    admin = _register(ADMIN)
    h = _auth_headers(ADMIN["email"], ADMIN["password"])
    r = client.put(
        f"/api/v1/adminpro/users/{admin['user']['id']}/password",
        json={"new_password": "abc"},
        headers=h,
    )
    assert r.status_code == 422, r.text
