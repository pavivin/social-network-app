import asyncio

from voices.app.auth.models import User
from voices.db.connection import Transaction


async def handle():
    async with Transaction():
        db_users = await User.get_all()

        for user in db_users:
            ...


asyncio.run(handle())
