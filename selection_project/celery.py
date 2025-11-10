# selection_project/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'selection_project.settings')

app = Celery('selection_project') # Usa el nombre de tu nuevo proyecto
app.config_from_object('selection_project.settings', namespace='CELERY')
app.autodiscover_tasks()