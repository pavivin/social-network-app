import asyncio

import firebase_admin
from celery import Celery
from firebase_admin import credentials

from voices.config import settings

app = Celery(settings.tasks_name, broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BACKEND_URL)
loop = asyncio.get_event_loop()

cred = credentials.Certificate(settings.FIREBASE_SECRETS)
app_firebase = firebase_admin.initialize_app(cred, name="Vizme_Backend")

from voices.broker.tasks import CELERY_IMPORTS

app.conf.update(tasks=CELERY_IMPORTS)
