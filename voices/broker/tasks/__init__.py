from voices.broker import app

from .notification import send_notification


@app.on_after_configure.connect
def test_task(sender, **kwargs):
    test.s("Look at me Hector")


@app.task
def test(arg):
    print(arg)


CELERY_IMPORTS = [test, send_notification, test_task]
