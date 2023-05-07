import uuid
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped

from voices.db.connection import auto_session
from voices.models import BaseDatetimeModel


class Initiative(BaseDatetimeModel):
    __tablename__ = "initiatives"

    class Category(StrEnum):
        PROBLEM = "PROBLEM"
        EVENT = "EVENT"
        DECIDE_TOGETHER = "DECIDE_TOGETHER"

    user_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    # TODO: to enum
    category: Mapped[str] = sa.Column(sa.String)
    # TODO: GeoAlchemy2
    # location = sa.Column()

    @staticmethod
    @auto_session
    async def get_by_friends(friends_list: list[uuid.UUID], category: Category = None, session: AsyncSession = None):
        query = sa.select(Initiative).where(Initiative.user_id.in_(friends_list))

        if category:
            query.where(Initiative.category == category)

        result = (await session.execute(query)).scalars().first()
        return result
