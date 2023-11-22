import asyncio

import requests

from voices.app.auth.models import User
from voices.db.connection import Transaction


async def handle():
    async with Transaction():
        db_users = await User.get_all_images()
        for image in db_users:
            content = requests.get(image).content
            content


asyncio.run(handle())
