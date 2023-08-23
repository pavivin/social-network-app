import asyncio

import sqlalchemy as sa
from uuid_extensions import uuid7

from voices.app.initiatives.models import User
from voices.db.connection import Transaction, db_session


async def main():
    async with Transaction():
        query = sa.select(User).order_by(User.created_at.asc())

        result = await db_session.get().execute(query)
        result = result.scalars().all()

        for item in result:
            item.id = uuid7()
            db_session.get().add(item)
            await db_session.get().commit()


asyncio.run(main())
