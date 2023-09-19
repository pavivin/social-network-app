import asyncio

from voices.app.auth.models import User
from voices.chat import delete_user, get_users
from voices.db.connection import Transaction


async def handle():
    async with Transaction():
        chat_users = await get_users()
        db_users = await User.get_all()
        db_users = set(db_users)
        for user in chat_users.json()["users"]:
            if user["emails"][0]["address"] not in db_users:
                await delete_user(user_id=user["username"])


asyncio.run(handle())
