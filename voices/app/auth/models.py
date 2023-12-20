import uuid
from datetime import date, datetime
from enum import StrEnum
from functools import lru_cache

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, load_only

from voices.db.connection import db_session
from voices.models import BaseDatetimeModel
from voices.utils import count_max_length

CITY_MAPPING = {  # TODO: to EN naming
    "Ярославль": 1,
    "Ростов": 2,
    "Тутаев": 3,
}


class User(BaseDatetimeModel):
    __tablename__ = "users"

    class Role(StrEnum):  # TODO: all enum to numbers
        CITIZEN = "citizen"
        GOVERNMENT = "government"

    class City(StrEnum):  # TODO: all enum to numbers
        YAROSLAVL = "Ярославль"
        ROSTOB = "Ростов"
        TUTAEV = "Тутаев"

        @classmethod
        @lru_cache
        def all(cls):
            return [e.value for e in cls]

    first_name: Mapped[str] = sa.Column(sa.String(length=50), nullable=True, default="Анонимный")
    last_name: Mapped[str] = sa.Column(sa.String(length=50), nullable=True, default="Пользователь")
    email: Mapped[str] = sa.Column(sa.String(length=254), unique=True, index=True, nullable=False)
    role: Mapped[str] = sa.Column(sa.String(length=count_max_length(Role)), nullable=False, server_default=Role.CITIZEN)
    image_url: Mapped[str] = sa.Column(
        sa.String(length=2000),
        nullable=True,
        default="https://storage.yandexcloud.net/my-city/06563fe7f2a779b280000970701fa57b.webp",
    )
    hashed_password: Mapped[str] = sa.Column(sa.String(length=128), nullable=False)
    city: Mapped[str] = sa.Column(sa.String(length=50), nullable=True)
    district: Mapped[str] = sa.Column(sa.String(length=50), nullable=True)
    birthdate: Mapped[date] = sa.Column(sa.Date, nullable=True)
    email_approved: Mapped[bool] = sa.Column(sa.Boolean, nullable=True, default=False)  # TODO: to server_default
    phone: Mapped[str] = sa.Column(sa.String, nullable=True, unique=True)
    friends_count: Mapped[int] = sa.Column(sa.Integer, server_default="0")

    @staticmethod
    async def get_all():
        query = sa.select(User)
        result = (await db_session.get().execute(query)).scalars().all()
        return result

    @staticmethod
    async def get_all_images():
        query = sa.select(User.id, User.image_url)
        result = await db_session.get().execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_email(email: str):
        query = (
            sa.select(User)
            .where(User.email == email)
            .options(load_only(User.id, User.email, User.role, User.hashed_password, User.deleted_at))
        )
        result = (await db_session.get().execute(query)).scalars().first()
        return result

    @staticmethod
    async def get_email_by_id(id: uuid.UUID):
        query = sa.select(User.email).where(User.id == id).where(User.deleted_at.is_(None))
        result = await db_session.get().execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(id: uuid.UUID):
        query = sa.select(User).where(User.id == id).where(User.deleted_at.is_(None))
        result = (await db_session.get().execute(query)).scalars().first()
        return result

    @staticmethod
    async def get_profile(user_id: uuid.UUID):
        query = sa.select(User).where(User.id == user_id)
        result = await db_session.get().execute(query)
        return result.scalars().first()

    @staticmethod
    async def insert_data(email: str, hashed_password: str, first_name: str, last_name: str, city: str) -> "User":
        query = (
            sa.insert(User)
            .values(email=email, hashed_password=hashed_password, first_name=first_name, last_name=last_name, city=city)
            .returning(User)
        )
        return (await db_session.get().execute(query)).scalar()

    @staticmethod
    async def update_profile(unset: dict, user_id: str):
        query = sa.update(User).values(**unset).where(User.id == user_id).returning(User)
        return (await db_session.get().execute(query)).scalar()

    @staticmethod
    async def delete_profile(user_id: str):
        query = sa.update(User).values(deleted_at=datetime.now()).where(User.id == user_id)
        return await db_session.get().execute(query)

    @staticmethod
    async def confirm_email(user_id: str):
        query = sa.update(User).values(email_approved=True).where(User.id == user_id)
        return await db_session.get().execute(query)

    @staticmethod
    async def search_by_pattern(pattern: str, city: str, last_id: str | None = None, is_total: bool = False):
        selected = sa.func.count(User.id) if is_total else User
        query = sa.select(selected).where(User.deleted_at.is_(None))
        if pattern:
            normalized_pattern = pattern.lower()
            query = query.where(
                sa.or_(  # TODO: optimize by search vector
                    sa.func.concat(User.first_name, " ", User.last_name).contains(normalized_pattern),
                    sa.func.concat(User.last_name, " ", User.first_name).contains(normalized_pattern),
                )
                & (User.city == city)  # TODO: city to indexed number
            )
        if last_id:
            query = query.where(User.id < last_id)

        if not is_total:
            query = query.limit(20).order_by(User.id.desc())

        result = await db_session.get().execute(query)
        if is_total:
            return result.scalar_one()
        return result.scalars().all()

    @staticmethod
    async def increment_friends_count(user_list: list[str]) -> int:
        query = (
            sa.update(User).where(User.id.in_(user_list)).values(friends_count=User.friends_count + 1).returning(User)
        )
        await db_session.get().scalar(query)

    @staticmethod
    async def decrement_friends_count(user_list: list[str]) -> int:
        query = (
            sa.update(User).where(User.id.in_(user_list)).values(friends_count=User.friends_count - 1).returning(User)
        )
        await db_session.get().scalar(query)
