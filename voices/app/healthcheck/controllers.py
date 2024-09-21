from fastapi import APIRouter

from voices.app.core.protocol import Response

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
