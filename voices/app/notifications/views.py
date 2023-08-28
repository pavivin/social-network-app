from datetime import datetime
from uuid import UUID

from voices.app.core.protocol import BaseModel


class NotificationView(BaseModel):
    id: UUID
    text: str
    avatar_url: str | None
    created_at: datetime
    status: str
    first_name: str
    last_name: str


class NotificationList(BaseModel):
    notifications: list[NotificationView]


class FirebaseAdd(BaseModel):
    firebase_token: str
