import uuid
from enum import StrEnum

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, joinedload, relationship

from voices.app.auth.models import User
from voices.config import settings
from voices.db.connection import db_session
from voices.models import BaseDatetimeModel
from voices.utils import count_max_length


class Initiative(BaseDatetimeModel):
    __tablename__ = "initiatives"

    class Category(StrEnum):
        PROBLEM = "PROBLEM"
        EVENT = "EVENT"
        DECIDE_TOGETHER = "DECIDE_TOGETHER"

    user_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", foreign_keys="Initiative.user_id")  # TODO: joinedload default
    city: Mapped[str] = sa.Column(sa.String(length=35))
    images: Mapped[JSONB] = sa.Column(JSONB)
    category: Mapped[str] = sa.Column(sa.String(length=count_max_length(Category)))
    location = sa.Column(Geometry("POINT"), nullable=True)
    title: Mapped[str] = sa.Column(sa.String(length=100), nullable=False)
    main_text: Mapped[str] = sa.Column(sa.String, nullable=False)
    likes_count: Mapped[int] = sa.Column(sa.Integer, server_default="0", nullable=False)
    comments_count: Mapped[int] = sa.Column(sa.Integer, server_default="0", nullable=False)
    reposts_count: Mapped[int] = sa.Column(sa.Integer, server_default="0", nullable=False)

    @classmethod
    async def get_feed(
        cls,
        city: str,
        category: Category = None,
        last_id: uuid.UUID | None = None,
    ):
        query = (
            sa.select(cls)
            .where((cls.city == city) & (cls.deleted_at.is_(None)))
            .limit(settings.DEFAULT_PAGE_SIZE)
            .options(joinedload(cls.user))
        )

        if category:
            query = query.where(cls.category == category)

        if last_id:
            query = query.where(cls.id > last_id)

        result = await db_session.get().execute(query)
        return result.scalars().all()


class Comment(BaseDatetimeModel):
    __tablename__ = "comments"

    main_text: Mapped[str] = sa.Column(sa.String, nullable=False)
    user_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", foreign_keys="Comment.user_id")
    initiative_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("initiatives.id"), nullable=False)
    initiative: Mapped[User] = relationship("Initiative", foreign_keys="Comment.initiative_id")
    parent_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("comments.id"), nullable=True)
    replies = relationship("Comment", foreign_keys="Comment.parent_id", uselist=True, lazy="joined")

    @classmethod
    async def post_comment(
        cls, main_text: str, initiative_id: uuid.UUID, user_id: uuid.UUID, reply_id: uuid.UUID | None = None
    ):
        query = sa.insert(cls).values(
            main_text=main_text, parent_id=reply_id, initiative_id=initiative_id, user_id=user_id
        )
        return await db_session.get().execute(query)

    @classmethod
    async def get_comments(cls, initiative_id: uuid.UUID, last_id: uuid.UUID | None = None):
        query = (
            sa.select(cls)
            .where((cls.initiative_id == initiative_id) & (cls.deleted_at.is_(None)) & (cls.parent_id.is_(None)))
            .order_by(cls.id.asc())
            .options(
                joinedload(cls.user, innerjoin=True),
                joinedload(cls.initiative),
                joinedload(cls.replies),
            )
            .limit(settings.DEFAULT_PAGE_SIZE)
        )

        if last_id:
            query = query.where(cls.id > last_id)

        result = await db_session.get().execute(query)
        return result.unique().scalars().all()
