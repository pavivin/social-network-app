import socketio
from aiohttp import web

sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)


async def index(request):
    """Serve the client-side application."""
    print("penis")


@sio.on("connect")
async def connect(sid, env):
    print("on connect")
    await sio.emit("You are connected", room=sid)


@sio.on("direct")
async def direct(sid, msg):
    print(f"direct {msg}")
    await sio.emit("event_name", msg, room=sid)  # we can send message to specific sid


@sio.on("broadcast")
async def broadcast(sid, msg):
    print(f"broadcast {msg}")
    await sio.emit("event_name", msg)  # or send to everyone


@sio.event
def disconnect(sid):
    print("disconnect ", sid)


app.router.add_get("/", index)
if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8000)
