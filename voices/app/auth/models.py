import uuid
from datetime import date
from enum import StrEnum
from functools import lru_cache

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, load_only

from voices.db.connection import db_session
from voices.models import BaseDatetimeModel
from voices.utils import count_max_length


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
        default="https://voices-city.ru/api/storage/064e74c0198f7159800002e35c77df4a.jpg",
    )
    hashed_password: Mapped[str] = sa.Column(sa.String(length=128), nullable=False)
    city: Mapped[str] = sa.Column(sa.String(length=50), nullable=True)
    district: Mapped[str] = sa.Column(sa.String(length=50), nullable=True)
    birthdate: Mapped[date] = sa.Column(sa.Date, nullable=True)
    email_approved: Mapped[bool] = sa.Column(sa.Boolean, nullable=True)
    phone: Mapped[str] = sa.Column(sa.String, nullable=True, unique=True)

    @staticmethod
    async def get_all():
        query = sa.select(User.email)
        result = (await db_session.get().execute(query)).scalars().all()
        return result

    @staticmethod
    async def get_by_email(email: str):
        query = (
            sa.select(User)
            .where(User.email == email)
            .options(load_only(User.id, User.email, User.role, User.hashed_password))
        )
        result = (await db_session.get().execute(query)).scalars().first()
        return result

    @staticmethod
    async def get_email_by_id(id: uuid.UUID):
        query = sa.select(User.email).where(User.id == id)
        result = await db_session.get().execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(id: uuid.UUID):
        query = sa.select(User).where(User.id == id)
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
    async def confirm_email(user_id: str):
        query = sa.update(User).values(email_approved=True).where(User.id == user_id)
        return await db_session.get().execute(query)

    @staticmethod
    async def search_by_pattern(pattern: str, city: str, last_id: str | None = None, is_total: bool = False):
        selected = sa.func.count(User.id) if is_total else User
        query = sa.select(selected)
        if pattern:
            normalized_pattern = pattern.lower()
            query = query.where(
                sa.or_(
                    sa.func.lower(User.first_name).contains(normalized_pattern),
                    sa.func.lower(User.last_name).contains(normalized_pattern),
                )
                & (User.city == city)  # TODO: city to indexed number
            )
        if last_id:
            query = query.where(User.id < last_id)
        result = await db_session.get().execute(query)
        if is_total:
            return result.scalar_one()
        return result.scalars().all()
