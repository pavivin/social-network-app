import uuid
from fastapi import APIRouter, Depends, Path

from voices.app.core.protocol import Response
from voices.auth.jwt_token import (
    JWTBearer,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from voices.db.connection import Transaction

from .models import FirebaseApp, Notification
from .views import FirebaseAdd, NotificationOut
from voices.app.auth.views import TokenData


router = APIRouter()


@router.post("/firebase-create")
async def add_token_device(body: FirebaseAdd,token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        token_exist = await FirebaseApp.token_exist(body.firebase_token)
        if not token_exist:
            await FirebaseApp.create(token.sub, body.firebase_token)
        return Response(code=201)

@router.get("/notification/{skip}/{limit}",response_model=NotificationOut)
async def create_card(
        skip: int = Path(...),
        limit: int = Path(...),
        token: TokenData = Depends(JWTBearer())
    ) -> Response[NotificationOut]:
        async with Transaction():
            notifications = await Notification.get_notifications(token.sub, limit, skip)
        return Response(payload=notifications)

@router.patch("/notification/{notification_id}")
async def read_notification(notification_id: uuid.UUID,token: TokenData = Depends(JWTBearer()), ) -> Response:
        async with Transaction():
            await Notification.read_notification(notification_id=notification_id)
        return Response()