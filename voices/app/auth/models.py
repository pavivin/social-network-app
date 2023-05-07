import uuid
from enum import StrEnum

from sqlalchemy import Column, String, insert, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped

from voices.db.connection import auto_session
from voices.models import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    class UserRole(StrEnum):
        USER = "USER"
        ADMIN = "ADMIN"

    id: Mapped[str] = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = Column(String, nullable=True)
    last_name: Mapped[str] = Column(String, nullable=True)
    email: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    role: Mapped[str] = Column(String, nullable=False, default=UserRole.USER)
    hashed_password: Mapped[str] = Column(String, nullable=False)

    @staticmethod
    @auto_session
    async def get_by_email(email: str, session: AsyncSession = None):
        query = select(User).where(User.email == email)
        result = (await session.execute(query)).scalars().first()
        return result

    @staticmethod
    @auto_session
    async def insert_data(email: str, hashed_password: str, session: AsyncSession = None):
        query = insert(User).values(
            email=email,
            hashed_password=hashed_password,
        )
        await session.execute(query)
        await session.commit()
