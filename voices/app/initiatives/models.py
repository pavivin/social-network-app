import uuid
from datetime import date
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
    ObjectNotFoundError,
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
        SURVEY = "SURVEY"
        PROJECT = "PROJECT"
        BUILDING = "BUILDING"

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

    class TagsCategory(StrEnum):
        PROBLEM = "Новость"
        EVENT = "Событие"
        DECIDE_TOGETHER = "Решаем вместе"
        SURVEY = "Опрос"
        PROJECT = "Проект"
        BUILDING = "Строительство"

    user_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", foreign_keys="Initiative.user_id")  # TODO: joinedload default
    city: Mapped[str] = sa.Column(sa.String(length=35))
    images: Mapped[JSONB] = sa.Column(JSONB)
    image_url: Mapped[str] = sa.Column(sa.String(length=2000), nullable=True)  # temp for Django
    category: Mapped[str] = sa.Column(sa.String(length=count_max_length(Category)))
    location = sa.Column(Geometry("POINT"), nullable=True)
    title: Mapped[str] = sa.Column(sa.String(length=100), nullable=False)
    main_text: Mapped[str] = sa.Column(sa.String, nullable=False)
    likes_count: Mapped[int] = sa.Column(sa.Integer, server_default="0", nullable=False)
    comments_count: Mapped[int] = sa.Column(sa.Integer, server_default="0", nullable=False)
    reposts_count: Mapped[int] = sa.Column(sa.Integer, server_default="0", nullable=False)
    status: Mapped[str] = sa.Column(sa.String(length=count_max_length(Status)), server_default=Status.ACTIVE)
    from_date: Mapped[date] = sa.Column(sa.Date())
    to_date: Mapped[date] = sa.Column(sa.Date())
    tags: Mapped[JSONB] = sa.Column(JSONB, nullable=True)
    ar_model: Mapped[str] = sa.Column(sa.String(length=2000), nullable=True)
    event_direction: Mapped[str] = sa.Column(sa.String(length=100), nullable=True)
    approved: Mapped[bool] = sa.Column(sa.Boolean, nullable=True)

    @classmethod
    async def update_likes_count(cls, initiative_id: str, count: int):
        query = (
            sa.update(Initiative)
            .where(Initiative.id == initiative_id)
            .values(likes_count=Initiative.likes_count + count)
        )
        await db_session.get().execute(query)

    @classmethod
    async def increment_comments_count(cls, initiative_id: str):
        query = (
            sa.update(Initiative)
            .where(Initiative.id == initiative_id)
            .values(comments_count=Initiative.comments_count + 1)
        )
        await db_session.get().execute(query)

    @classmethod
    async def create(
        cls,
        city,
        user_id,
        images,
        title,
        main_text,
        category: Category,
        location: GeometryPoint,
        ar_model: str = None,
        event_direction: str = None,
        from_date: date = None,
        to_date: date = None,
    ):
        tags = [cls.TagsCategory[category]]
        if ar_model:
            tags.append("AR")
        if from_date and to_date:
            tags.append("Активно")

        tags = tags[:2]

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
                ar_model=ar_model,
                event_direction=event_direction,
                tags=tags,
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
        search: str | None = None,
        is_total: bool = False,
        is_maps: bool = False,
    ):
        selected = sa.func.count(cls.id) if is_total else cls
        query = sa.select(selected).where(
            (cls.city == city) & (cls.deleted_at.is_(None)) & (Initiative.approved.is_(True))
        )

        if not is_total:
            query = query.options(
                joinedload(cls.user).load_only(User.first_name, User.last_name, User.image_url, User.id)
            ).order_by(cls.id.desc())

        if not is_maps:
            query = query.limit(settings.DEFAULT_PAGE_SIZE)

        if search:
            query = query.where(cls.title.icontains(search))

        # TODO: unify filters
        if category:
            query = query.where(cls.category == category)

        if last_id:
            query = query.where(cls.id < last_id)

        if status:
            query = query.where(cls.status == status)

        if role:
            query = query.where(cls.user.has(role=role))

        result = await db_session.get().execute(query)
        if is_total:
            return result.scalar_one()
        return result.scalars().all()

    @staticmethod
    async def get_actual(city: str, is_total: bool = False):
        selected = sa.func.count(Initiative.id) if is_total else Initiative
        current_date = date.today()
        query = sa.select(selected).where(
            (Initiative.city == city)
            & (Initiative.deleted_at.is_(None))
            & (Initiative.approved.is_(True))
            & (Initiative.from_date <= current_date)
            & (Initiative.to_date >= current_date)
        )

        if not is_total:
            query = (
                query.limit(settings.ACTUAL_PAGE_SIZE)
                .options(
                    joinedload(Initiative.user).load_only(User.first_name, User.last_name, User.id, User.image_url)
                )
                .order_by(Initiative.id.desc())
            )

        result = await db_session.get().execute(query)
        if is_total:
            return result.scalar_one()
        return result.scalars().all()

    @classmethod
    async def get_favorites(cls, city: str, user_id: str, last_id: str = None, is_total: bool = False):
        selected = sa.func.count(cls.id) if is_total else cls
        query = (
            sa.select(selected)
            .join(InitiativeLike, cls.id == InitiativeLike.initiative_id)
            .where(
                (Initiative.city == city)
                & (
                    Initiative.deleted_at.is_(None)
                    & (Initiative.approved.is_(True))
                    & (InitiativeLike.user_id == user_id)
                )
            )
        )

        if not is_total:
            query = (
                query.limit(settings.DEFAULT_PAGE_SIZE)
                .options(
                    joinedload(Initiative.user).load_only(User.first_name, User.last_name, User.id, User.image_url)
                )
                .order_by(cls.id.desc())
            )

        if last_id:
            query = query.where(cls.id < last_id)

        result = await db_session.get().execute(query)
        if is_total:
            return result.scalar_one()
        return result.scalars().all()

    @classmethod
    async def get_my(cls, city: str, user_id: str, last_id: str = None, is_total: bool = False):
        selected = sa.func.count(cls.id) if is_total else cls
        query = sa.select(selected).where(
            (Initiative.city == city)
            & (Initiative.deleted_at.is_(None) & (Initiative.approved.is_(True)) & (Initiative.user_id == user_id))
        )

        if not is_total:
            query = query.limit(settings.DEFAULT_PAGE_SIZE).options(joinedload(Initiative.user)).order_by(cls.id.desc())

        if last_id:
            query = query.where(cls.id < last_id)

        result = await db_session.get().execute(query)
        if is_total:
            return result.scalar_one()
        return result.scalars().all()


class Comment(BaseDatetimeModel):
    __tablename__ = "comments"

    main_text: Mapped[str] = sa.Column(sa.String, nullable=False)
    user_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", foreign_keys="Comment.user_id")
    initiative_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("initiatives.id"), nullable=False)
    initiative: Mapped[Initiative] = relationship("Initiative", foreign_keys="Comment.initiative_id")
    parent_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("comments.id"), nullable=True)
    replies = relationship("Comment", foreign_keys="Comment.parent_id", uselist=True, lazy="joined")

    @staticmethod
    async def get(value):
        query = sa.select(Comment).where(Comment.id == value)
        try:
            result = (await db_session.get().execute(query)).unique().scalar_one()
            return result
        except Exception as e:
            raise ObjectNotFoundError from e

    @classmethod
    async def post_comment(
        cls, main_text: str, initiative_id: uuid.UUID, user_id: uuid.UUID, reply_id: uuid.UUID | None = None
    ):
        query = sa.insert(cls).values(
            main_text=main_text, parent_id=reply_id, initiative_id=initiative_id, user_id=user_id
        )
        return await db_session.get().execute(query)

    @staticmethod
    async def get_comments(initiative_id: uuid.UUID, last_id: uuid.UUID | None = None, is_total: bool = False):
        selected = sa.func.count(Comment.id) if is_total else Comment
        query = sa.select(selected).where(
            (Comment.initiative_id == initiative_id) & (Comment.deleted_at.is_(None)) & (Comment.parent_id.is_(None))
        )

        if not is_total:
            query = (
                query.order_by(Comment.id.desc())
                .options(
                    joinedload(Comment.user, innerjoin=True),
                    joinedload(Comment.initiative),
                    joinedload(Comment.replies).joinedload(Comment.user),
                )
                .limit(settings.DEFAULT_PAGE_SIZE)
            )

        if last_id:
            query = query.where(Comment.id < last_id)

        result = await db_session.get().execute(query)
        if is_total:
            return result.scalar_one()
        return result.unique().scalars().all()


class InitiativeLike(BaseModel):
    __tablename__ = "initiatives_likes"

    __table_args__ = (sa.UniqueConstraint("user_id", "initiative_id", name="_user_initiative_idx"),)

    user_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", foreign_keys="InitiativeLike.user_id")
    initiative_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("initiatives.id"), nullable=False)
    initiative: Mapped[User] = relationship("Initiative", foreign_keys="InitiativeLike.initiative_id")
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())

    @staticmethod
    async def get_count_liked(initiative_id: str):
        query = sa.select(sa.func.count(InitiativeLike.initiative_id)).where(
            InitiativeLike.initiative_id == initiative_id
        )
        result = await db_session.get().execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_liked(initiative_list: list[str], user_id: str):
        query = sa.select(InitiativeLike.initiative_id).where(
            (InitiativeLike.initiative_id.in_(initiative_list)) & (InitiativeLike.user_id == user_id)
        )
        result = await db_session.get().execute(query)
        return result.scalars().all()

    @staticmethod
    async def is_like_exists(initiative_id: uuid.UUID, user_id: uuid.UUID):
        query = sa.select(InitiativeLike.id).where(
            (InitiativeLike.initiative_id == initiative_id) & (user_id == user_id)
        )
        result = await db_session.get().execute(query)
        return result.scalar_one()

    @staticmethod
    async def post_like(initiative_id: uuid.UUID, user_id: uuid.UUID):
        try:
            query = sa.insert(InitiativeLike).values(
                InitiativeLike.initiative_id == initiative_id, InitiativeLike.user_id == user_id
            )
            return await db_session.get().execute(query)
        except IntegrityError:
            raise AlreadyLikedError

    @staticmethod
    async def delete_like(initiative_id: uuid.UUID, user_id: uuid.UUID):
        query = (
            sa.delete(InitiativeLike)
            .where((InitiativeLike.initiative_id == initiative_id) & (InitiativeLike.user_id == user_id))
            .returning(InitiativeLike.id)
        )
        result: sa.CursorResult = await db_session.get().execute(query)
        if not result.scalars().all():
            raise AlreadyUnlikedError
