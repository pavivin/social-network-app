import asyncio

from celery import Celery

from vizme.config import settings

app = Celery(settings.tasks_name, broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BACKEND_URL)
loop = asyncio.get_event_loop()  # global loop is used for asynchronous tasks below
