import asyncio
from voices.app.auth.models import User

from voices.app.friends.models import Friend
from voices.db.connection import Transaction


async def handle():
    async with Transaction() as tr:
        user_list = await User.get_all()
        for user in user_list:
            friends = await Friend.get_friends(user_id=user.id, is_total=True)
            user.friends_count = friends
            await tr.session.commit()


asyncio.run(handle())
