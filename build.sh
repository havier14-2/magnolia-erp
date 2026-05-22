#!/usr/bin/env bash
# Salir inmediatamente si ocurre un error
set -o errexit

echo "Instalando dependencias..."
pip install -r requirements.txt

echo "Recolectando archivos estáticos (CSS/JS)..."
python manage.py collectstatic --no-input

echo "Ejecutando migraciones de Base de Datos..."
python manage.py migrate