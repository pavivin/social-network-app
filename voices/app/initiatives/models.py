import uuid
from enum import StrEnum

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped

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
    city: Mapped[str] = sa.Column(sa.String(length=35))

    images: Mapped[JSONB] = sa.Column(JSONB)
    category: Mapped[str] = sa.Column(sa.String(length=count_max_length(Category)))
    location = sa.Column(Geometry("POINT"), nullable=True)
    title: Mapped[str] = sa.Column(sa.String(length=100), nullable=False)
    main_text: Mapped[str] = sa.Column(sa.String, nullable=False)
    likes_count: Mapped[int] = sa.Column(sa.Integer, server_default="0", nullable=False)
    comments_count: Mapped[int] = sa.Column(sa.Integer, server_default="0", nullable=False)

    @staticmethod
    async def get_feed(
        city: str,
        category: Category = None,
        last_id: uuid.UUID | None = None,
    ):
        query = sa.select(Initiative).where(Initiative.city == city).where(Initiative.deleted_at.is_(None))

        if category:
            query = query.where(Initiative.category == category)

        if last_id:
            query = query.where(Initiative.id > last_id)

        result = await db_session.get().execute(query)
        return result.scalars().all()
