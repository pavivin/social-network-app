import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped

from voices.db.base import Base
from voices.db.connection import db_session
from voices.exceptions import ObjectNotFoundError


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid.uuid4)

    @classmethod
    async def get(cls, value: Any):
        query = sa.select(cls).where(cls.id == value)
        try:
            result = (await db_session.get().execute(query)).scalar_one()
            return result
        except Exception as e:
            raise ObjectNotFoundError from e


class BaseDatetimeModel(BaseModel):
    __abstract__ = True

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
