import uuid
from datetime import datetime
from enum import StrEnum

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError

from voices.app.auth.models import User
from voices.app.notifications.models import FirebaseApp, Notification
from voices.broker import app, app_firebase, loop
from voices.db.connection import Transaction
from voices.utils import get_minify_image


class EventName(StrEnum):
    LIKE = "like"
    REQUEST_FRENDS = "request_frends"
    ACCEPT_FRENDS = "accept_frends"
    SHARE = "share"
    COMMENT = "comment"
    ANSWERED = "answered"
    CHANGE_STATUS = "change_status"
    POST_CREATED = "post_created"
    POST_APPROVED = "post_approved"
    POST_DECLINED = "post_declined"
    ALREADY_FRIENDS = "already_friends"


status_text = {
    EventName.LIKE: "Оценил вашу запись",
    EventName.REQUEST_FRENDS: "Хочет добавить вас в друзья",
    EventName.ACCEPT_FRENDS: "Принял вашу заявку",
    EventName.ALREADY_FRIENDS: "Вы приняли заявку в друзья",
    EventName.SHARE: "Поделился вашей записью",
    EventName.COMMENT: "Оставил комментарий под вашей записью",
    EventName.ANSWERED: "Ответил вам",
    EventName.CHANGE_STATUS: "Изменился статус интересовавшей вас проблемы",
    EventName.POST_CREATED: "Ваша запись находится на модерации",
    EventName.POST_APPROVED: "Ваша запись одобрена",
    EventName.POST_DECLINED: "Ваша запись отклонена",
}

assert len(EventName) == len(status_text)  # TODO: to tests


async def firebase_notifications(
    user_id_send: str,
    user_id_get: str,
    status: EventName,
    initiative_image: str = None,
    initiative_id: uuid.UUID = None,
):
    async with Transaction():
        tokens = await FirebaseApp.get_tokens(user_id_get)
        user: User = await User.get_by_id(user_id_send)
        text = status_text[status]
        data_send = {
            "text": text,
            "picture": get_minify_image(user.image_url),  # TODO: remove
            "avatar_url": get_minify_image(user.image_url),
            "time": datetime.now().isoformat(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "type": status,
        }

        if initiative_id:
            data_send["initiative_id"] = str(initiative_id)
        if initiative_image:
            initiative_image = get_minify_image(initiative_image)
            data_send["initiative_image"] = initiative_image

        await Notification.create(
            owner_id=user_id_get,
            text=text,
            avatar_url=get_minify_image(user.image_url),
            first_name=user.first_name,
            last_name=user.last_name,
            type=status,
            user_id=user_id_send,
            initiative_image=initiative_image,
            initiative_id=initiative_id,
        )
        if status == EventName.ACCEPT_FRENDS:
            await Notification.update_already_friends(
                user_id=user_id_send,
                old_status=status,
                new_status=EventName.ALREADY_FRIENDS,
                new_text=status_text[EventName.ALREADY_FRIENDS],
            )
        notification_image = get_minify_image(initiative_image) or get_minify_image(user.image_url)
        response = None
        for token in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=text,
                        body=text,
                        image=notification_image,
                    ),
                    data=data_send,
                    token=token,
                )
                response = messaging.send(message, app=app_firebase)
            except FirebaseError:
                ...
    return response


@app.task(name="send_notification")
def send_notification(
    user_id_send: str, user_id_get: str, status: str, initiative_id=None, initiative_image=None
) -> int:
    return loop.run_until_complete(
        firebase_notifications(
            user_id_send=user_id_send,
            user_id_get=user_id_get,
            status=status,
            initiative_image=initiative_image,
            initiative_id=initiative_id,
        )
    )
