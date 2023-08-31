from datetime import datetime, timezone
from enum import StrEnum

from firebase_admin import messaging

from voices.app.auth.models import User
from voices.app.notifications.models import FirebaseApp, Notification
from voices.broker import app, app_firebase, loop
from voices.db.connection import Transaction


class EventName(StrEnum):
    LIKE = "like"
    REQUEST_FRENDS = "request_frends"
    ACCEPT_FRENDS = "accept_frends"
    SHARE = "share"
    COMMENT = "comment"
    ANSWERED = "answered"
    CHANGE_STATUS = "change_status"


status_text = {
    EventName.LIKE: "Оценил вашу запись",
    EventName.REQUEST_FRENDS: "Хочет добавить вас в друзья",
    EventName.ACCEPT_FRENDS: "Принял вашу заявку",
    EventName.SHARE: "Поделился вашей записью",
    EventName.COMMENT: "Оставил комментарий под вашей записью",
    EventName.ANSWERED: "Ответил вам",
    EventName.CHANGE_STATUS: "Изменился статус интересовавшей вас проблемы",
}


async def firebase_notifications(user_id_send: str, user_id_get: str, status: EventName):
    async with Transaction():
        tokens = await FirebaseApp.get_tokens(user_id_get)

        user: User = await User.get_by_id(user_id_send)
        text = status_text[status]
        time = datetime.now(tz=timezone.utc)
        data_send = {
            "text": text,
            "picture": user.image_url,
            "time": time.isoformat(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "type": status,
        }
        await Notification.create(
            owner_id=user_id_get,
            text=text,
            avatar_url=user.image_url,
            first_name=user.first_name,
            last_name=user.last_name,
            type=status,
            user_id=user_id_send,
        )
        response = None
        for token in tokens:
            message = messaging.Message(
                data=data_send,
                token=token,
            )
            response = messaging.send(message, app=app_firebase)
    return response


@app.task(name="send_notification")
def send_notification(user_id_send: str, user_id_get: str, status: str) -> int:
    return loop.run_until_complete(
        firebase_notifications(user_id_send=user_id_send, user_id_get=user_id_get, status=status)
    )
