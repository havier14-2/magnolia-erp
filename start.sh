#!/usr/bin/env bash
# Salir inmediatamente si ocurre un error
set -o errexit

echo "Iniciando el Worker de Celery en segundo plano..."
# El símbolo '&' al final es la magia: manda el proceso a ejecutarse en la sombra
celery -A magnolia worker --loglevel=info &

echo "Iniciando el Servidor Web Gunicorn..."
# Este proceso se queda en primer plano manteniendo el servidor vivo
gunicorn magnolia.wsgi:application