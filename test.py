import json

import requests
from websockets.sync.client import connect

SOCKET_URL = "ws://89.108.65.101:3000/websocket"


def login_api():
    return requests.post(
        "https://voices-city.ru/api/login",
        json={
            "email": "pashok@example.com",
            "password": "string",
        },
    ).json()


def _request(data: dict):
    msg = json.dumps(data)
    print(f"> SENT {msg}")
    websocket.send(msg)
    message = websocket.recv()
    print(f"> RECEIVED: {message}")
    return json.loads(message)


def connect_chat():
    _request(
        data={
            "msg": "connect",
            "version": "1",
            "support": ["1"],
        }
    )


def login_chat(token: str):
    _request(
        data={
            "msg": "method",
            "method": "login",
            "params": [{"resume": token}],
            "id": "42",
        }
    )


def create_chat(user_id: str):
    return _request(
        data={
            "msg": "method",
            "method": "createDirectMessage",
            "id": "42",
            "params": [user_id],
        }
    )


def send_message(room_id: str, msg: str = "foo"):
    return _request(
        data={
            "msg": "method",
            "method": "sendMessage",
            "id": "423",
            "params": [{"rid": room_id, "msg": msg}],
        }
    )


def load_history(user_id: str, last_date: str, limit: str = 50):
    return _request(
        data={
            "msg": "method",
            "method": "loadHistory",
            "id": "42",
            "params": [user_id, {"$date": 0}, limit, {"$date": last_date}],
        }
    )


def get_rooms():
    return _request(
        {
            "msg": "method",
            "method": "rooms/get",
            "id": "42",
            "params": [{"$date": 0}],
        }
    )


with connect(SOCKET_URL) as websocket:
    login_data = login_api()
    auth_token = login_data["payload"]["rocketchatAuthToken"]
    user_id = login_data["payload"]["rocketchatUserId"]
    # ----------------- API -----------------
    connect_chat()
    login_chat(token=auth_token)
    # ----------------- CONNECT TO SOCKET -----------------
    chat_data = create_chat(user_id=user_id)
    room_id = chat_data["result"]["id"]
    msg_info = send_message(room_id=room_id)
    last_date = msg_info["date"]
    load_history(user_id=user_id, last_date=last_date)
    # ----------------- CHAT -----------------
    _request
