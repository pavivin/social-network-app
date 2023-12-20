import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, load_only, relationship

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
    user: Mapped[User] = relationship("User", foreign_keys="Friend.user_id", lazy="joined")
    friend_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    friend: Mapped[User] = relationship("User", foreign_keys="Friend.friend_id", lazy="joined")
    relationship_type = sa.Column(sa.String(length=12), server_default=RelationshipType.NOT_APPROVED)
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())

    @staticmethod
    async def get_friend(profile_id: str, user_id: str):  # TODO optimize
        query = (
            sa.select(Friend)
            .where(sa.and_(Friend.user_id == profile_id, Friend.friend_id == user_id))
            .options(load_only(Friend.relationship_type, Friend.user_id, Friend.friend_id))
        )
        result = await db_session.get().execute(query)
        relationship_type = result.scalar_one_or_none()
        if relationship_type:
            return relationship_type

        query = (
            sa.select(Friend)
            .where(sa.and_(Friend.friend_id == profile_id, Friend.user_id == user_id))
            .options(load_only(Friend.relationship_type, Friend.user_id, Friend.friend_id))
        )
        result = await db_session.get().execute(query)
        relationship_type = result.scalar_one_or_none()
        return relationship_type

    @staticmethod
    async def get_friends(user_id: str, last_id: str | None = None, is_total: bool = False, pattern: str | None = None):
        selected = sa.func.count(Friend.id) if is_total else Friend
        query = (
            sa.select(selected)
            .where(sa.or_(Friend.user_id == user_id) & (Friend.relationship_type == RelationshipType.FRIEND))
            .where(User.deleted_at.is_(None))
        )
        if not is_total:
            query = query.join(Friend.friend)
        if last_id:
            query = query.where(Friend.id < last_id)

        if pattern:
            normalized_pattern = pattern.lower()
            query = query.where(
                sa.or_(
                    sa.func.concat(sa.func.lower(User.first_name), " ", sa.func.lower(User.last_name)).contains(
                        normalized_pattern
                    ),
                    sa.func.concat(sa.func.lower(User.last_name), " ", sa.func.lower(User.first_name)).contains(
                        normalized_pattern
                    ),
                )
            )
        result = await db_session.get().execute(query)
        if is_total:
            friends_count = result.scalar_one()
        else:
            friends_friends = result.scalars().all()

        # second part
        # TODO: to one query
        selected = sa.func.count(Friend.id) if is_total else Friend
        query = sa.select(selected).where(
            sa.or_(Friend.friend_id == user_id) & (Friend.relationship_type == RelationshipType.FRIEND)
        )
        if not is_total:
            query = query.join(Friend.user)
        if last_id:
            query = query.where(Friend.id < last_id)

        if pattern:
            normalized_pattern = pattern.lower()
            query = query.where(
                sa.or_(
                    sa.func.lower(User.first_name).contains(normalized_pattern),
                    sa.func.lower(User.last_name).contains(normalized_pattern),
                )
            )

        result = await db_session.get().execute(query)
        if is_total:
            return friends_count + result.scalar_one()
        friends_users = result.scalars().all()

        return friends_friends + friends_users

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
