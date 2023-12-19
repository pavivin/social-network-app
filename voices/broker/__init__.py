import asyncio

import firebase_admin
from celery import Celery, signals
from firebase_admin import credentials
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

from voices.config import settings

app = Celery(settings.tasks_name, broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BACKEND_URL)
loop = asyncio.get_event_loop()

cred = credentials.Certificate(settings.FIREBASE_SECRETS)
app_firebase = firebase_admin.initialize_app(cred)


@signals.celeryd_init.connect
def init_sentry(**_kwargs):
    if not settings.DEBUG:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[CeleryIntegration(monitor_beat_tasks=True)],
            traces_sample_rate=1.0,
        )


from voices.broker.tasks import CELERY_IMPORTS  # noqa: E402

app.conf.update(tasks=CELERY_IMPORTS)
