#!/usr/bin/env bash
# Arranque del backend en Linux/macOS (B13). Equivalente a run.ps1.
#
# Idempotente: crea el venv si falta, instala deps, copia .env desde el ejemplo
# la primera vez y levanta la API. Correr desde la raiz del repo:  ./run.sh
set -euo pipefail

cd "$(dirname "$0")"

VENV=".venv"
PY="$VENV/bin/python"

# 1) venv
if [ ! -d "$VENV" ]; then
  echo "==> Creando entorno virtual en $VENV"
  python3 -m venv "$VENV"
fi

# 2) dependencias
echo "==> Instalando dependencias"
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet -r requirements.txt

# 3) .env
if [ ! -f ".env" ]; then
  echo "==> No hay .env; copiando desde .env.example"
  cp .env.example .env
  echo "!!  Edita .env y define ADMIN_TOKEN antes de la demo (el proceso no"
  echo "!!  levanta con ADMIN_TOKEN vacio). Genera uno con:"
  echo "!!    $PY -c \"import secrets; print(secrets.token_urlsafe(24))\""
fi

# 4) API
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
echo "==> Levantando API en http://$HOST:$PORT (docs en /docs)"
exec "$PY" -m uvicorn app.main:app --reload --host "$HOST" --port "$PORT"
