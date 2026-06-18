#!/usr/bin/env bash
# Salir inmediatamente si ocurre un error
set -o errexit

echo "Ejecutando la siembra de datos para la presentación directamente en Neon..."
python manage.py seed_demo

echo "Iniciando el Worker de Celery en modo ultraligero (pool=solo)..."
# --pool=solo evita que Celery clone procesos, ahorrando más de 100MB de RAM.
# --concurrency=1 fuerza a usar un solo hilo.
celery -A magnolia worker --pool=solo --concurrency=1 --loglevel=info &

echo "Iniciando el Servidor Web Gunicorn optimizado..."
# Forzamos a Gunicorn a usar un solo trabajador web
gunicorn magnolia.wsgi:application --workers 1 --threads 2