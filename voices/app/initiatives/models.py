import uuid
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped

from voices.db.connection import auto_session
from voices.models import BaseDatetimeModel
from voices.utils import count_max_length


class Initiative(BaseDatetimeModel):
    __tablename__ = "initiatives"

    class Category(StrEnum):
        PROBLEM = "PROBLEM"
        EVENT = "EVENT"
        DECIDE_TOGETHER = "DECIDE_TOGETHER"

    user_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    city: Mapped[str] = sa.Column(sa.String(length=35))

    images: Mapped[JSONB] = sa.Column(JSONB)
    category: Mapped[str] = sa.Column(sa.String(length=count_max_length(Category)))  # TODO: to enum
    # TODO: GeoAlchemy2
    # location = sa.Column()

    @staticmethod
    @auto_session
    async def get_feed(
        city: str,
        category: Category = None,
        session: AsyncSession = None,
        last_id: uuid.UUID | None = None,
    ):
        query = sa.select(Initiative).where(Initiative.city == city)

        if category:
            query = query.where(Initiative.category == category)

        if last_id:
            query = query.where(Initiative.id > last_id)

        result = (await session.execute(query)).scalars().first()
        return result
