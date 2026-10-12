#!/usr/bin/env bash
# Arranca backend + frontend del SVSPSystem y verifica que respondan.
# Pensado para: terminal del Codespace Y arranque automático (devcontainer).
# Uso:  bash .devcontainer/start-all.sh
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
LOGDIR="$ROOT/.devcontainer/logs"
mkdir -p "$LOGDIR"

ok=1
say() { echo "[start-all] $*"; }

# --- 1. Backend: dependencias + .env -------------------------------------
if [ ! -f "$BACKEND/.env" ]; then
  say "ERROR: falta $BACKEND/.env (cópialo de backend/.env.example con tu DATABASE_URL)."
  say "El backend NO arrancará hasta crearlo."
  ok=0
else
  say ".env del backend encontrado."
fi

if [ -f "$BACKEND/requirements.txt" ]; then
  say "Instalando dependencias Python (puede tardar la primera vez)..."
  pip install -q -r "$BACKEND/requirements.txt" || ok=0
fi

# --- 2. Backend: migraciones + seed (no duplica) --------------------------
if [ "$ok" -eq 1 ]; then
  cd "$BACKEND"
  python apply_migrations.py || ok=0
  python seed_adminpro.py || true
fi

# --- 3. Backend: arrancar si el puerto está libre --------------------------
if ss -tlnp 2>/dev/null | grep -q ":8000" || netstat -tlnp 2>/dev/null | grep -q ":8000"; then
  say "Puerto 8000 ocupado: se reutiliza el proceso existente (no se duplica)."
else
  say "Arrancando backend en :8000 ..."
  cd "$BACKEND"
  nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
    >"$LOGDIR/backend.log" 2>&1 &
  echo $! > "$LOGDIR/backend.pid"
fi

# --- 4. Frontend: dependencias + arranque -----------------------------------
cd "$FRONTEND"
if [ ! -d node_modules ]; then
  say "Instalando dependencias Node (solo primera vez)..."
  npm install || ok=0
fi
if ss -tlnp 2>/dev/null | grep -q ":5173" || netstat -tlnp 2>/dev/null | grep -q ":5173"; then
  say "Puerto 5173 ocupado: se reutiliza el proceso existente."
else
  say "Arrancando frontend en :5173 ..."
  nohup npm run dev >"$LOGDIR/frontend.log" 2>&1 &
  echo $! > "$LOGDIR/frontend.pid"
fi

# --- 5. Verificación ---------------------------------------------------------
say "Esperando servicios (máx 60s)..."
for i in $(seq 1 30); do
  B=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo 000)
  F=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5173/ 2>/dev/null || echo 000)
  if [ "$B" != "000" ] && [ "$F" != "000" ]; then
    break
  fi
  sleep 2
done
say "Backend :8000 -> HTTP $B | Frontend :5173 -> HTTP $F"
say "Logs: $LOGDIR/backend.log y $LOGDIR/frontend.log"
if [ "$B" = "000" ] || [ "$F" = "000" ]; then
  say "ALGO FALLÓ: revisa los logs de arriba. Comandos útiles:"
  say "  backend : tail -30 $LOGDIR/backend.log"
  say "  frontend: tail -30 $LOGDIR/frontend.log"
  exit 1
fi
say "LISTO. Abre el frontend desde la pestaña PORTS (Forwarded Address del 5173)."
