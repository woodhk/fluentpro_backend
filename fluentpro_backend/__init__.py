# Import Celery app to ensure it's always loaded when Django starts
from workers.celery_app import app as celery_app

__all__ = ('celery_app',)