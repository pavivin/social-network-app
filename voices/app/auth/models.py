import uuid
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped

from voices.db.connection import db_session
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
    image_url: Mapped[str] = sa.Column(sa.String(length=2000), nullable=True)
    hashed_password: Mapped[str] = sa.Column(sa.String(length=128), nullable=False)

    @staticmethod
    async def get_by_email(email: str):
        query = sa.select(User).where(User.email == email)
        result = (await db_session.get().execute(query)).scalars().first()
        return result

    @staticmethod
    async def get_by_id(id: uuid.UUID):
        query = sa.select(User).where(User.id == id)
        result = (await db_session.get().execute(query)).scalars().first()
        return result

    @staticmethod
    async def insert_data(email: str, hashed_password: str) -> uuid.UUID:
        query = sa.insert(User).values(email=email, hashed_password=hashed_password).returning(User.id)
        return (await db_session.get().execute(query)).scalar()

    @staticmethod
    async def update_profile(unset: dict):
        query = sa.update(User).values(**unset).returning(User)
        return (await db_session.get().execute(query)).scalar()

    @staticmethod
    async def search_by_pattern(pattern: str):
        normalized_pattern = pattern.lower()
        query = sa.select(User).where(
            sa.or_(
                sa.func.lower(User.first_name).contains(normalized_pattern),
                sa.func.lower(User.last_name).contains(normalized_pattern),
            )
        )
        result = (await db_session.get().execute(query)).scalars().all()
        return result
