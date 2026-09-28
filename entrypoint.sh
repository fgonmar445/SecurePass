#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# SecurePass - Entrypoint de producción
# Espera a que PostgreSQL esté disponible, aplica migraciones, recolecta
# los archivos estáticos y finalmente lanza el servidor Gunicorn.
# ---------------------------------------------------------------------------
set -e

HOST="${POSTGRES_HOST:-db}"
PORT="${POSTGRES_PORT:-5432}"

echo "Esperando a que PostgreSQL esté disponible en ${HOST}:${PORT}..."
until nc -z "$HOST" "$PORT"; do
  echo "PostgreSQL no está listo todavía. Reintentando en 1 segundo..."
  sleep 1
done
echo "PostgreSQL está listo."

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
