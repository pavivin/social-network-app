import uuid

from fastapi import APIRouter, Depends

from voices.app.auth.views import TokenData
from voices.app.core.protocol import Response
from voices.auth.jwt_token import JWTBearer
from voices.db.connection import Transaction

from .models import FirebaseApp, Notification
from .views import FirebaseAdd, NotificationOut

router = APIRouter()


@router.post("/firebase-create")
async def add_token_device(body: FirebaseAdd, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        token_exist = await FirebaseApp.token_exist(body.firebase_token)
        if not token_exist:
            await FirebaseApp.create(token.sub, body.firebase_token)
        return Response(code=201)


@router.get("/notifications", response_model=NotificationOut)
async def get_notifications(
    last_id: uuid.UUID = None, token: TokenData = Depends(JWTBearer())  # to last_id
) -> Response[NotificationOut]:
    async with Transaction():
        notifications = await Notification.get_notifications(user_id=token.sub, last_id=last_id)
    return Response(payload=notifications)


@router.patch("/notifications/{notification_id}")
async def read_notification(
    notification_id: uuid.UUID,
    token: TokenData = Depends(JWTBearer()),
) -> Response:
    async with Transaction():
        await Notification.read_notification(notification_id=notification_id)
    return Response()
