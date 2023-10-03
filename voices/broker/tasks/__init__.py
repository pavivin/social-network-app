from voices.broker import app
from voices.mail.confirm_email import confirm_email_task

from .notification import send_notification

CELERY_IMPORTS = [send_notification, confirm_email_task]
