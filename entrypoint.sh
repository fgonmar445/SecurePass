#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# SecurePass - Entrypoint de producción
#
# Espera a que la base de datos configurada (Docker Compose local o Neon/
# Supabase en producción, según DATABASE_URL) esté disponible, aplica
# migraciones, recolecta los archivos estáticos y lanza Gunicorn en el
# puerto que exija la plataforma (Render inyecta PORT; en local usamos 8000).
# ---------------------------------------------------------------------------
set -e

echo "Esperando a que la base de datos esté disponible..."
python <<'PYEOF'
import os
import sys
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connections
from django.db.utils import OperationalError

conn = connections["default"]
max_attempts = 30

for attempt in range(1, max_attempts + 1):
    try:
        conn.cursor()
        print("Base de datos disponible.")
        break
    except OperationalError as exc:
        print(f"Base de datos no disponible todavía (intento {attempt}/{max_attempts}): {exc}")
        if attempt == max_attempts:
            print("No se pudo conectar a la base de datos. Abortando.")
            sys.exit(1)
        time.sleep(2)
PYEOF

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

PORT="${PORT:-8000}"
echo "Iniciando Gunicorn en el puerto ${PORT}..."
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers 3 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
