from uuid import UUID
from datetime import date, datetime
from voices.app.core.protocol import BaseModel

class NotificationOut(BaseModel):
    id: UUID
    text: str
    avatar_url: str | None
    created_at: datetime
    status: str
    first_name: str
    last_name: str

class FirebaseAdd(BaseModel):
    firebase_token: str