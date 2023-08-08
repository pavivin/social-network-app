import uuid
from datetime import datetime
from enum import StrEnum

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, joinedload, relationship

from voices.app.auth.models import User
from voices.app.core.exceptions import (
    AlreadyLikedError,
    AlreadyUnlikedError,
    NotFoundError,
)
from voices.app.core.protocol import GeometryPoint
from voices.config import settings
from voices.db.connection import db_session
from voices.models import BaseDatetimeModel, BaseModel
from voices.utils import count_max_length


class Initiative(BaseDatetimeModel):
    __tablename__ = "initiatives"

    # TODO: to lowercase
    class CitizenCategory(StrEnum):
        PROBLEM = "PROBLEM"
        EVENT = "EVENT"
        DECIDE_TOGETHER = "DECIDE_TOGETHER"

    class Category(StrEnum):
        PROBLEM = "PROBLEM"
        EVENT = "EVENT"
        DECIDE_TOGETHER = "DECIDE_TOGETHER"
        SURVEY = "SURVEY"
        PROJECT = "PROJECT"
        BUILDING = "BUILDING"

    class Status(StrEnum):
        ACTIVE = "active"
        SOLVED = "solved"

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
    status: Mapped[str] = sa.Column(sa.String(length=count_max_length(Status)), server_default=Status.ACTIVE)
    from_date: Mapped[datetime] = sa.Column(sa.DateTime())
    to_date: Mapped[datetime] = sa.Column(sa.DateTime())

    @classmethod
    async def update_likes_count(cls, initiative_id: str, count: int):
        query = sa.update(cls).values(likes_count=cls.likes_count + count).where(initiative_id == initiative_id)
        await db_session.get().execute(query)

    @classmethod
    async def increment_comments_count(cls, initiative_id: str):
        query = sa.update(cls).values(comments_count=cls.comments_count + 1).where(initiative_id == initiative_id)
        await db_session.get().execute(query)

    @classmethod
    async def create(cls, city, user_id, images, title, main_text, category, location: GeometryPoint):
        query = (
            sa.insert(Initiative)
            .values(
                city=city,
                user_id=user_id,
                images=images,
                title=title,
                main_text=main_text,
                category=category.value,
                location=GeometryPoint.to_str(location),
            )
            .returning(Initiative.id)
        )
        result = await db_session.get().execute(query)
        return result.scalars().first()

    @classmethod
    async def select(cls, initiative_id: str):
        query = (
            sa.select(cls).where((cls.deleted_at.is_(None) & (cls.id == initiative_id))).options(joinedload(cls.user))
        )
        result = await db_session.get().execute(query)
        initiative = result.scalars().first()
        if not initiative:
            raise NotFoundError()
        return initiative

    @classmethod
    async def get_feed(
        cls,
        city: str,
        category: Category | None = None,
        last_id: uuid.UUID | None = None,
        status: Status | None = None,
        role: User.Role | None = None,
    ):
        query = (
            sa.select(cls)
            .where((cls.city == city) & (cls.deleted_at.is_(None)))
            .limit(settings.DEFAULT_PAGE_SIZE)
            .options(joinedload(cls.user))
        )

        # TODO: unify filters
        if category:
            query = query.where(cls.category == category)

        if last_id:
            query = query.where(cls.id > last_id)

        if status:
            query = query.where(cls.status == status)

        if role:
            query = query.where(cls.user.has(role=role))

        result = await db_session.get().execute(query)
        return result.scalars().all()

    @classmethod
    async def get_favorites(cls, city: str, user_id: str, last_id: str):
        query = (
            sa.select(Initiative)
            .join(InitiativeLike, cls.id == InitiativeLike.initiative_id)
            .where((Initiative.city == city) & (Initiative.deleted_at.is_(None) & (InitiativeLike.user_id == user_id)))
            .limit(settings.DEFAULT_PAGE_SIZE)
            .options(joinedload(Initiative.user))
        )

        if last_id:
            query = query.where(cls.id > last_id)

        result = await db_session.get().execute(query)
        return result.scalars().all()

    @classmethod
    async def get_my(cls, city: str, user_id: str, last_id: str):
        query = (
            sa.select(Initiative)
            .where((Initiative.city == city) & (Initiative.deleted_at.is_(None) & (Initiative.user_id == user_id)))
            .limit(settings.DEFAULT_PAGE_SIZE)
            .options(joinedload(Initiative.user))
        )

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

    @staticmethod
    async def get_comments(initiative_id: uuid.UUID, last_id: uuid.UUID | None = None):
        query = (
            sa.select(Comment)
            .where(
                (Comment.initiative_id == initiative_id)
                & (Comment.deleted_at.is_(None))
                & (Comment.parent_id.is_(None))
            )
            .order_by(Comment.id.asc())
            .options(
                joinedload(Comment.user, innerjoin=True),
                joinedload(Comment.initiative),
                joinedload(Comment.replies).joinedload(Comment.user),
            )
            .limit(settings.DEFAULT_PAGE_SIZE)
        )

        if last_id:
            query = query.where(Comment.id > last_id)

        result = await db_session.get().execute(query)
        return result.unique().scalars().all()


class InitiativeLike(BaseModel):
    __tablename__ = "initiatives_likes"

    __table_args__ = (sa.UniqueConstraint("user_id", "initiative_id", name="_user_initiative_idx"),)

    user_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", foreign_keys="InitiativeLike.user_id")
    initiative_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("initiatives.id"), nullable=False)
    initiative: Mapped[User] = relationship("Initiative", foreign_keys="InitiativeLike.initiative_id")
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())

    @classmethod
    async def get_liked(cls, initiative_list: list[str], user_id: str):
        query = sa.select(cls.initiative_id).where((cls.initiative_id.in_(initiative_list)) & (cls.user_id == user_id))
        result = await db_session.get().execute(query)
        return result.scalars().all()

    @classmethod
    async def is_like_exists(cls, initiative_id: uuid.UUID, user_id: uuid.UUID):
        query = sa.select(cls.id).where((initiative_id == initiative_id) & (user_id == user_id))
        result = await db_session.get().execute(query)
        return result.scalar_one()

    @classmethod
    async def post_like(cls, initiative_id: uuid.UUID, user_id: uuid.UUID):
        try:
            query = sa.insert(cls).values(initiative_id=initiative_id, user_id=user_id)
            return await db_session.get().execute(query)
        except IntegrityError:
            raise AlreadyLikedError

    @classmethod
    async def delete_like(cls, initiative_id: uuid.UUID, user_id: uuid.UUID):
        query = sa.delete(cls).where((initiative_id == initiative_id) & (user_id == user_id)).returning(cls.id)
        result: sa.CursorResult = await db_session.get().execute(query)
        if not result.scalars().all():
            raise AlreadyUnlikedError
