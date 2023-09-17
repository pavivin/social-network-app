import asyncio

from voices.db.connection import Transaction


async def handle():
    async with Transaction():
        ...


asyncio.run(handle)
