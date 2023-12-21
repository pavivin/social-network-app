from fastapi import APIRouter

from voices.app.core.protocol import Response

from firebase_admin import messaging

import firebase_admin
from firebase_admin import credentials

from voices.config import settings

router = APIRouter()


cred = credentials.Certificate(settings.FIREBASE_SECRETS)
app_firebase = firebase_admin.initialize_app(cred, name="test")


@router.get(
    "/healthz",
    response_model=Response,
)
async def get_healthcheck():
    return Response()


@router.post("/test/notification", response_model=Response)
async def test_notification(token: str, is_notification: bool = False):
    if is_notification:
        message = messaging.Message(
            notification=messaging.Notification(
                title="Хочет добавить вас в друзья",
                body="Хочет добавить вас в друзья",
                image="https://storage.yandexcloud.net/my-city/06563fe7f2a779b280000970701fa57b-min.webp",
            ),
            data={
                "text": "Хочет добавить вас в друзья",
                "picture": "https://storage.yandexcloud.net/my-city/06563fe7f2a779b280000970701fa57b-min.webp",
                "avatar_url": "https://storage.yandexcloud.net/my-city/06563fe7f2a779b280000970701fa57b-min.webp",
                "time": "2023-12-21T22:12:08.098441",
                "first_name": "Павел",
                "last_name": "Ивин",
                "type": "request_frends",
            },
            token=token,
        )
    else:
        message = messaging.Message(
            # notification=messaging.Notification(
            #     title="Хочет добавить вас в друзья",
            #     body="Хочет добавить вас в друзья",
            #     image="https://storage.yandexcloud.net/my-city/06563fe7f2a779b280000970701fa57b-min.webp",
            # ),
            data={
                "text": "Хочет добавить вас в друзья",
                "picture": "https://storage.yandexcloud.net/my-city/06563fe7f2a779b280000970701fa57b-min.webp",
                "avatar_url": "https://storage.yandexcloud.net/my-city/06563fe7f2a779b280000970701fa57b-min.webp",
                "time": "2023-12-21T22:12:08.098441",
                "first_name": "Павел",
                "last_name": "Ивин",
                "type": "request_frends",
            },
            token=token,
        )
    response = messaging.send(message, app=app_firebase)
    return Response(message=str(response))
