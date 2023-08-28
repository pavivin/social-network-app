import uuid

import sqlalchemy as sa
from uuid_extensions import uuid7

from voices.db.connection import db_session
from voices.models import BaseModel


class NotificationStatus:
    UNREADED = "UNREADED"
    READED = "READED"


class Notification(BaseModel):
    __tablename__ = "notifications"
    owner_id = sa.Column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, default=uuid7
    )
    text = sa.Column("text", sa.VARCHAR(350), nullable=True)
    status = sa.Column(sa.String(length=8), server_default=NotificationStatus.UNREADED, nullable=False)
    avatar_url = sa.Column("avatar", sa.VARCHAR(500), nullable=True)
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())
    first_name = sa.Column("first_name", sa.VARCHAR(50), nullable=True)
    last_name = sa.Column("last_name", sa.VARCHAR(50), nullable=True)
    type = sa.Column(sa.String(length=13), nullable=False)  # TODO: to number

    @classmethod
    async def read_notification(cls, notification_id: uuid.UUID):
        query = (
            sa.update(Notification).values(status=NotificationStatus.READED).where(Notification.id == notification_id)
        )
        await db_session.get().execute(query)

    @classmethod
    async def create(cls, owner_id: uuid.UUID, text: str, avatar_url: str, first_name: str, last_name: str, type: str):
        query = sa.insert(Notification).values(
            owner_id=owner_id,
            text=text,
            avatar_url=avatar_url,
            first_name=first_name,
            last_name=last_name,
            type=type,
        )
        await db_session.get().execute(query)

    @classmethod
    async def get_notifications(cls, user_id: uuid.UUID, last_id: str = None):
        query = sa.select(Notification).where(Notification.owner_id == user_id).order_by(Notification.created_at.desc())

        if last_id:
            query.where(Notification.id < last_id)
        result = await db_session.get().execute(query)
        return result.scalars().all()


class FirebaseApp(BaseModel):
    __tablename__ = "firebase_token"

    owner = sa.Column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, default=uuid.uuid4
    )
    token = sa.Column("token", sa.VARCHAR(254), nullable=False)

    @classmethod
    async def create(cls, owner: uuid.UUID, token: str) -> None:
        query = sa.insert(FirebaseApp).values(owner=owner, token=token).returning(FirebaseApp.id)
        await db_session.get().execute(query)

    @classmethod
    async def get_tokens(cls, owner: uuid.UUID) -> uuid.UUID:
        query = sa.select(FirebaseApp.token).where(FirebaseApp.owner == owner)
        result = await db_session.get().execute(query)
        return result.scalars().all()

    @classmethod
    async def token_exist(cls, token: str) -> bool:
        query = sa.select(FirebaseApp.token).where(FirebaseApp.token == token)
        result = (await db_session.get().execute(query)).scalars().first()
        return result
