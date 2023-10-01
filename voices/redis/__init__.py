from uuid import uuid4

import redis.asyncio as redis

from voices.config import settings


class Redis:
    con: redis.Redis
    email_expires = 60 * 60 * 24  # 1 day in seconds

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(Redis, cls).__new__(cls)
        return cls.instance

    @classmethod
    async def connect(cls) -> None:
        cls.con = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    @classmethod
    async def disconnect(cls) -> None:
        if cls.con:
            await cls.con.close()

    @classmethod
    async def generate_confirm_email_token(cls, user_id: str) -> str:
        token = uuid4().hex
        await cls.con.set(f"ce:{user_id}", value=token, ex=cls.email_expires)  # ce - confirm email
        return token

    @classmethod
    async def get_confirm_email_token(cls, user_id: str) -> str | None:
        token = await cls.con.get(f"ce:{user_id}")
        return token

    @classmethod
    async def delete_confirm_email_token(cls, user_id: str) -> str | None:
        token = await cls.con.delete(f"ce:{user_id}")
        return token
