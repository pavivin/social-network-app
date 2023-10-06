from voices.broker import app

from .notification import send_notification

CELERY_IMPORTS = [send_notification]
