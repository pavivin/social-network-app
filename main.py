import socketio
from blacksheep import Application, Request, json
from blacksheep.server.openapi.v3 import OpenAPIHandler
from openapidocs.v3 import Info

from vizme import exceptions
from vizme.app.healthcheck.controllers import CatsController
from vizme.logger import logger
from vizme.protocol import Response

app = Application()

app.register_controllers([CatsController])

docs = OpenAPIHandler(info=Info(title="VizMe API", version="0.0.1"), ui_path="/api/docs")
docs.bind_app(app)

app.use_cors(
    allow_methods="*",
    allow_origins="*",
    allow_headers="* Authorization",
    max_age=300,
)

sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
# wrap with ASGI application
socket_app = socketio.ASGIApp(sio)
app.mount("/api/chat", socket_app)


# @sio.event()
# def my_custom_event(sid, data):
#     sio.emit("my event", {"data": "foobar"})


@sio.on("connect")
async def connect(sid, env):
    sio.emit("my event", {"data": "foobar"})
    print("New Client Connected to This id :" + " " + str(sid))


@app.exception_handler(Exception)
async def uvicorn_base_exception_handler(self, request: Request, exc: Exception):
    logger.debug(exc)
    error = exceptions.ServerError(message=str(exc))
    return json(Response(code=error.status_code, message=error.message, body=error.payload).dict())


@app.exception_handler(exceptions.ApiException)
async def unicorn_api_exception_handler(self, request: Request, exc: exceptions.ApiException):
    logger.debug(exc.message)

    return json(
        Response(
            code=exc.status_code,
            message=exc.message,
            body=exc.payload,
        ).dict(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5000)
