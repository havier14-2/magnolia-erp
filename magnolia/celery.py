import os
from celery import Celery

# Establecer el módulo de settings por defecto de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'magnolia.settings')

app = Celery('magnolia')

# Usar una cadena en la configuración para que el worker no tenga que
# serializar el objeto de configuración (namespace='CELERY' significa que
# todas las variables relacionadas con celery en settings.py deben empezar con 'CELERY_')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas asíncronas en todas las apps instaladas (como 'inventory')
app.autodiscover_tasks()