import json
import time
import uuid

import requests
from websockets.sync.client import connect

SOCKET_URL = "ws://89.223.126.166:3000/websocket"


def login_api():
    return requests.post(
        "https://my-city.pro/api/login",
        json={
            "email": "user@example.com",
            "password": "string",
        },
    ).json()


def _request(data: dict):
    msg = json.dumps(data)
    print(f"> SENT {msg}")
    websocket.send(msg)
    message = websocket.recv()
    print(f"> RECEIVED: {message}")
    if message == '{"msg":"ping"}':
        websocket.send('{"msg":"pong"}')
        message = websocket.recv()
        print(f"> RECEIVED: {message}")
    if message.startswith('{"msg":"updated","methods"'):
        message = websocket.recv()
        print(f"> RECEIVED: {message}")

    return json.loads(message)


def connect_chat():
    _request(data={"msg": "connect", "version": "1", "support": ["1"]})


def login_chat(token: str):
    return _request(
        data={
            "msg": "method",
            "method": "login",
            "params": [{"resume": token}],
            "id": uuid.uuid4().hex,
        }
    )


def create_chat(user_id: str):
    _request(
        data={"msg": "method", "method": "createDirectMessage", "id": uuid.uuid4().hex, "params": [user_id]},
    )
    message = websocket.recv()
    message = websocket.recv()
    return json.loads(message)


def send_message(room_id: str, msg: str = "foo"):
    return _request(
        data={
            "msg": "method",
            "method": "sendMessage",
            "id": uuid.uuid4().hex,
            "params": [{"rid": room_id, "msg": msg}],
        }
    )


def load_history(room_id: str, last_date: str, limit: str = 50):
    # https://developer.rocket.chat/reference/api/realtime-api/method-calls/rooms/load-history
    return _request(
        data={
            "msg": "method",
            "method": "loadHistory",
            "id": uuid.uuid4().hex,
            "params": [room_id, {"$date": last_date}, limit, {"$date": 0}],
        }
    )


def stream_messages(room_id: str):
    # https://developer.rocket.chat/reference/api/realtime-api/subscriptions/streamlivechatroom
    return _request(
        data={
            "msg": "sub",
            "id": uuid.uuid4().hex,
            "name": "stream-room-messages",
            "params": [room_id, False],
        }
    )


def stream_notify_room(room_id: str):
    return _request(
        {
            "msg": "sub",
            "id": uuid.uuid4().hex,
            "name": "stream-notify-room",
            "params": [f"{room_id}/message", False],
        }
    )


def stream_notify_user(user_id: str):
    return _request(
        {
            "msg": "sub",
            "id": uuid.uuid4().hex,
            "name": "stream-notify-all",
            "params": [f"{user_id}/event", False],
        }
    )


def get_rooms():
    return _request(
        {
            "msg": "method",
            "method": "rooms/get",
            "id": uuid.uuid4().hex,
            "params": [{"$date": 0}],
        }
    )


def get_message(token: str):
    return _request(
        {
            "msg": "method",
            "method": "getSingleMessage",
            "id": uuid.uuid4().hex,
            "params": [token],
        },
    )


with connect(SOCKET_URL) as websocket:
    login_data = login_api()
    auth_token = login_data["payload"]["rocketchatAuthToken"]
    user_id = login_data["payload"]["rocketchatUserId"]
    # ----------------- API -----------------
    connect_chat()
    chat_login_data = login_chat(token=auth_token)
    # chat_token = chat_login_data['id']
    # ----------------- CONNECT TO SOCKET -----------------
    chat_data = create_chat(user_id=user_id)
    # room_id = chat_data["result"]["rid"]
    room_id = "cRGBWwEhwajxwuXHSqzqHjiscX2ZQyTW5S"
    # msg_info = send_message(room_id=room_id)
    # last_date = msg_info["result"]["ts"]["$date"]
    # load_history(room_id=room_id, last_date=last_date)
    # ----------------- CHAT -----------------

    while True:
        # result = stream_notify_user(user_id=user_id)
        response = stream_notify_room(room_id=room_id)
        response
        print("json", response)
        get_message(token=auth_token)
        time.sleep(1)
    # ROOMS
    get_rooms()
