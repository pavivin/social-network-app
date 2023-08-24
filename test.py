import asyncio

import sqlalchemy as sa
from uuid_extensions import uuid7

from voices.app.initiatives.models import Initiative, User
from voices.db.connection import Transaction, db_session


async def main():
    async with Transaction():
        query = sa.select(User).order_by(User.created_at.asc())

        result = await db_session.get().execute(query)
        result = result.scalars().all()
        for item in result:
            session = db_session.get()
            query = sa.select(Initiative).where(Initiative.user_id == item.id)
            user_id = uuid7()
            item.id = user_id

            session.add(item)
            await session.commit()

        # for init, user_id in init_mapping.items():
        #     session = db_session.get()
        #     initiative: Initiative = Initiative.get(init)
        #     initiative.user_id = user_id
        #     session.add(initiative)
        #     await session.commit()


asyncio.run(main())
