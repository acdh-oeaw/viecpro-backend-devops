
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apis.settings.dev")
# =, backend="redis://127.0.0.1:6380", broker="redis://127.0.0.1:6380")
app = Celery("apis")
# app.conf.broker_url = "redis://127.0.0.1:6380"
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
