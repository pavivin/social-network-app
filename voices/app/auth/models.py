import uuid
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped

from voices.db.connection import auto_session
from voices.models import BaseDatetimeModel
from voices.utils import count_max_length


class User(BaseDatetimeModel):
    __tablename__ = "users"

    class UserRole(StrEnum):
        USER = "USER"
        ADMIN = "ADMIN"

    first_name: Mapped[str] = sa.Column(sa.String(length=50), nullable=True)
    last_name: Mapped[str] = sa.Column(sa.String(length=50), nullable=True)
    email: Mapped[str] = sa.Column(sa.String(length=254), unique=True, index=True, nullable=False)
    role: Mapped[str] = sa.Column(sa.String(length=count_max_length(UserRole)), nullable=False, default=UserRole.USER)
    hashed_password: Mapped[str] = sa.Column(sa.String, nullable=False)

    @staticmethod
    @auto_session
    async def get_by_email(email: str, session: AsyncSession = None):
        query = sa.select(User).where(User.email == email)
        result = (await session.execute(query)).scalars().first()
        return result

    @staticmethod
    @auto_session
    async def get_by_id(id: uuid.UUID, session: AsyncSession = None):
        query = sa.select(User).where(User.id == id)
        result = (await session.execute(query)).scalars().first()
        return result

    @staticmethod
    @auto_session
    async def insert_data(email: str, hashed_password: str, session: AsyncSession = None) -> uuid.UUID:
        query = sa.insert(User).values(email=email, hashed_password=hashed_password).returning(User.id)
        return (await session.execute(query)).scalar()

    @staticmethod
    @auto_session
    async def update_profile(unset: dict, session: AsyncSession = None):
        query = sa.update(User).values(**unset).returning(User)
        return (await session.execute(query)).scalar()

    @staticmethod
    @auto_session
    async def search_by_pattern(pattern: str, session: AsyncSession):
        query = sa.select(User).where(sa.func.lower(User.first_name).contains(pattern.lower()))
        result = (await session.execute(query)).scalars().all()
        return result
