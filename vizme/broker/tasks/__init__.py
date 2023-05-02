from vizme.broker import app


@app.on_after_configure.connect
def test_task(sender, **kwargs):
    test.s("Look at me Hector")


@app.task
def test(arg):
    print(arg)
