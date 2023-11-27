from voices.broker import app  # noqa: F401

from .notification import send_notification

CELERY_IMPORTS = [send_notification]
