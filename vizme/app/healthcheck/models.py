import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, VARCHAR

from vizme.db.base import Base
from vizme.db.connection import db_session


class Cats(Base):
    __tablename__ = "cats"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = sa.Column("name", VARCHAR(15), nullable=False)

    @classmethod
    async def create(cls, name: str):
        session = db_session.get()
        query = sa.insert(cls).values(name=name)
        await session.execute(query)
        await session.commit()

    @classmethod
    async def update(cls, name: str):
        session = db_session.get()
        query = sa.update(cls).values(name=name)
        await session.execute(query)
        await session.commit()
