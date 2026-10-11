# SVSP System — Sistema Web de Gestión de Asistencia y Visitas

Backend **FastAPI** + Frontend **React/Vite**. Producción usa **Neon (PostgreSQL)**.
Los tests de CI usan **SQLite temporal** (no tocan datos reales).

## Estructura

```
backend/            # FastAPI (routers en backend/app, core en backend/core)
frontend/           # React + Vite (fetch relativo /api + proxy a :8000)
svsp/frontend/      # Segundo frontend (axios + VITE_API_URL)
svsp/backend/       # Variante de backend
```

## Arranque rápido (desarrollo)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt

# Crear backend/.env (OBLIGATORIO — sin esto la app se niega a arrancar).
# Ver backend/.env.example como plantilla. NUNCA commitear el .env real.
cat > .env <<'EOF'
DATABASE_URL="postgresql://USUARIO:CLAVE@HOST:5432/svsp"
SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
ADMIN_EMAIL="admin@svsp.local"
ADMIN_PASSWORD="Admin123!"
ADMIN_FULL_NAME="Administrador SVSP"
EOF

python -c "import core.models; from core.database import Base, engine; Base.metadata.create_all(bind=engine); print('tables-ok')"
python seed_adminpro.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> En bases de datos **existentes** (Neon) hay que aplicar además las
> migraciones `backend/migrations/NNN_*.sql` en orden, con
> `psql "$DATABASE_URL" -f backend/migrations/NNN_*.sql` o pegando el
> contenido en el editor SQL de Neon. Son idempotentes (`IF NOT EXISTS`).
> En bases **nuevas** basta `create_all` + seed.

Debe terminar con `Application startup complete.` Documentación: `http://localhost:8000/docs`.

### 2. Frontend (`frontend/`)

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173 — el proxy /api reenvía al backend :8000
```

## GitHub Codespaces

- El navegador **no alcanza `localhost:8000`** (ese `localhost` es tu máquina).
  El frontend usa rutas relativas `/api/...` y el proxy de Vite las reenvía
  dentro del Codespace. No hardcodees `http://localhost:8000` en el código.
- CORS ya permite `https://*.app.github.dev` (ver `backend/app/main.py`).
- Expón los puertos **5173 y 8000** como **Public** en la pestaña PORTS.
- Si el nombre del Codespace cambia, actualiza `CORS_ORIGINS` en `backend/.env`.

## Usuarios y contraseñas

```bash
# Crear / verificar el admin (usa backend/.env para DATABASE_URL)
cd backend
python seed_adminpro.py        # idempotente: no duplica si ya existe

# Restablecer la clave de un usuario existente (la pide por argumento, no queda guardada)
python reset_admin_password.py admin@svsp.local 'NuevaClave123!'
```

Un AdminPRO también puede cambiar la clave de cualquier usuario vía API
(sin exponerla nunca en respuestas ni logs):

```bash
curl -X PUT http://localhost:8000/api/v1/adminpro/users/3/password \
  -H "Authorization: Bearer <TOKEN_ADMINPRO>" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "NuevaClave123!"}'
```

## Seguridad (obligatorio)

- **NUNCA** commitees `.env`, claves API, passwords ni connection strings.
  Están ignorados en `.gitignore` y hay pre-commit con `gitleaks` que bloquea secretos.
- Si una credencial real llega a git: **rótala de inmediato** en el proveedor
  (Neon → Roles → reset password) y actualiza tu `.env` local. Quitarla del
  código no la borra del historial.
- Instalar hooks: `pip install pre-commit && pre-commit install`.

## Diagnóstico en 2 minutos

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `No se pudo conectar al servidor` | Backend apagado o puerto sin Forward | Arrancar Uvicorn; pestaña PORTS → Forwarded |
| `HTTP 502` en `...-8000.app.github.dev` | Nada escucha en el 8000 | Arrancar backend; matar zombies (`ss -tlnp \| grep 8000`) |
| `address already in use` | Proceso viejo (docker-proxy, Uvicorn zombie) | `docker ps` → `docker stop/rm`; o `kill -9 <PID>` |
| `Credenciales incorrectas` (401) | Clave o usuario mal | Reset con `reset_admin_password.py`. **Esto confirma que SÍ hay conexión** |
| `password authentication failed` (Neon) | Clave del rol rotada/inválida | Rotar en Neon y actualizar `DATABASE_URL` en `.env` |
| `db-ok: localhost:5432` | `.env` no cargado | Debe estar en `backend/.env` (la config lo busca por ruta absoluta) |
| Swagger 404 pero login funciona | Puerto en Private para externos | PORTS → Public. El login funcionando manda sobre el Swagger |

## CI

Cada push/PR a `main`/`develop` corre `backend/tests` (SQLite) en GitHub Actions.
Ver `.github/workflows/ci.yml`. Si el CI está en rojo, no mergear.
