import socketio

sio = socketio.Client(logger=True, engineio_logger=True)


@sio.event
def connect():
    print('connection established')


@sio.event
def message(data):
    print('message received with ', data)
    sio.emit('my response', {'response': 'my response'})


@sio.event
def disconnect():
    print('disconnected from server')


sio.connect('http://localhost:5000/api/chat', namespaces=['/chat'])
sio.wait()