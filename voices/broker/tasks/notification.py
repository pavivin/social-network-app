import random
from datetime import datetime, timezone
from typing import List
from enum import Enum

from firebase_admin import messaging

from voices.app.auth.models import Notification, User
from voices.broker import app, app_firebase, loop
from voices.db.connection import Transaction

class EventName(str, Enum):
    like = "like"
    request = "request_frends"
    accept = "accept_frends"
    share = "share"
    comment = "comment"
    answered = "answered"
    change_status = "change_status"


async def firebase_notifications(tokens: List[str], user_id_send: str, user_id_get: str, title: str,status : EventName):
    async with Transaction():
        user: User = await User.get_by_id(user_id_send)
        first_name, last_name = user.first_name or "user", user.last_name or random.randint(a=0, b=99999)
        match status:
            case "like":
                data_send = {
                    "text": "Оценил вашу запись",
                    "picture": f"{user.picture_url}",
                    "time": str(datetime.now(tz=timezone.utc)),
                    "first_name": first_name,
                    "last_name": f"{last_name}",
                    "type":  status,
                }
            case "request_frends":
                data_send = {
                    "text": "Хочет добавить вас в друзья ",
                    "picture": f"{user.picture_url}",
                    "time": str(datetime.now(tz=timezone.utc)),
                    "first_name": first_name,
                    "last_name": f"{last_name}",
                    "type":  status,
                }
            case "accept_frends":
                data_send = {
                    "text": "Принял вашу заявку",
                    "picture": f"{user.picture_url}",
                    "time": str(datetime.now(tz=timezone.utc)),
                    "first_name": first_name,
                    "last_name": f"{last_name}",
                    "type":  status,
                }
            case "share":
                data_send = {
                    "text": "Поделился вашей записью",
                    "picture": f"{user.picture_url}",
                    "time": str(datetime.now(tz=timezone.utc)),
                    "first_name": first_name,
                    "last_name": f"{last_name}",
                    "type":  status,
                }
            case "comment":
                data_send = {
                    "text": "Оставил комментарий под вашей записью",
                    "picture": f"{user.picture_url}",
                    "time": str(datetime.now(tz=timezone.utc)),
                    "first_name": first_name,
                    "last_name": f"{last_name}",
                    "type":  status,
                }
            case "answered":
                data_send = {
                    "text": "Ответил вам",
                    "picture": f"{user.picture_url}",
                    "time": str(datetime.now(tz=timezone.utc)),
                    "first_name": first_name,
                    "last_name": f"{last_name}",
                    "type":  status,
                }
            case "change_status":
                data_send = {
                    "text": "Изменился статус интересовавшей вас проблемы",
                    "picture": f"{user.picture_url}",
                    "time": str(datetime.now(tz=timezone.utc)),
                    "first_name": first_name,
                    "last_name": f"{last_name}",
                    "type":  status,
                }
            case _:
                return "Something's wrong with the status Notification"
        await Notification.create(user_id_get, str(data_send["text"]), user.picture_url, first_name, f"{last_name}",status.title)
        for token in tokens:
            message = messaging.Message(
                data=data_send,
                token=token,
            )
            response = messaging.send(message, app=app_firebase)
    return response


@app.task(name="send_notification")
def send_notification(tokens: List[str], user_id_send: str, user_id_get: str, title: str, time_limit=70) -> int:
    return loop.run_until_complete(firebase_notifications(tokens, user_id_send, user_id_get, title))
