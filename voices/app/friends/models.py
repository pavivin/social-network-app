import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, joinedload, relationship

from voices.app.auth.models import User
from voices.db.connection import db_session
from voices.models import BaseModel


class RelationshipType:
    FRIEND = "FRIEND"  # добавлен взаимно
    NOT_APPROVED = "NOT_APPROVED"  # ещё не одобрен
    FOLLOWER = "FOLLOWER"  # подписчик
    DECLINED = "DECLINED"  # отклонена


class Friend(BaseModel):
    __tablename__ = "users_friends"

    __table_args__ = (sa.UniqueConstraint("user_id", "friend_id", name="_user_friend_idx"),)

    user_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", foreign_keys="Friend.user_id")
    friend_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    friend: Mapped[User] = relationship("User", foreign_keys="Friend.friend_id")
    relationship_type = sa.Column(sa.String(length=12), server_default=RelationshipType.NOT_APPROVED)
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())

    @classmethod
    async def get_friends(cls, user_id: str):
        query = (
            sa.select(Friend)
            .where(
                sa.or_(Friend.user_id == user_id, Friend.friend_id == user_id)
                & (Friend.relationship_type == RelationshipType.FRIEND)
            )
            .options(joinedload(cls.friend).load_only(User.first_name, User.last_name, User.image_url, User.id))
        )
        result = (await db_session.get().execute(query)).scalars().all()
        return result

    @classmethod
    async def add_friend(cls, user_id: str, friend_id: str):
        query = sa.insert(Friend).values(user_id=friend_id, friend_id=user_id)
        result = await db_session.get().execute(query)
        return result

    @classmethod
    async def approve_friend(cls, user_id: str, friend_id: str):
        query = (
            sa.update(Friend)
            .values(relationship_type=RelationshipType.FRIEND)
            .where((Friend.user_id == user_id) & (Friend.friend_id == friend_id))
        )
        result = await db_session.get().execute(query)
        return result

    @classmethod
    async def remove_friend(cls, user_id: str, friend_id: str):
        query = (
            sa.update(Friend)
            .values(relationship_type=RelationshipType.FOLLOWER)
            .where((Friend.user_id == user_id) & (Friend.friend_id == friend_id))
        )
        result = await db_session.get().execute(query)
        return result
