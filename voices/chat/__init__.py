import uuid

import httpx
from async_lru import alru_cache

from voices.config import settings

CREATE_USER_URL = settings.ROCKETCHAT_URL + "/api/v1/users.create"
LOGIN_USER_URL = settings.ROCKETCHAT_URL + "/api/v1/login"


async def create_user(user_id: uuid.UUID, email: str):
    response = await __login_superuser()
    json_response = response.json()
    superuser_id = json_response["data"]["userId"]
    superuser_auth_token = json_response["data"]["authToken"]

    async with httpx.AsyncClient() as client:
        return await client.post(
            CREATE_USER_URL,
            json={
                "email": email,
                "password": user_id.hex,
                "username": user_id.hex,
                "name": email,
            },
            headers={
                "X-Auth-Token": superuser_auth_token,
                "X-User-Id": superuser_id,
            },
        )


async def login_user(user_id: uuid.UUID):
    async with httpx.AsyncClient() as client:
        return await client.post(
            LOGIN_USER_URL,
            json={
                "user": user_id.hex,
                "password": user_id.hex,
            },
        )


@alru_cache(maxsize=1)
async def __login_superuser():
    async with httpx.AsyncClient() as client:
        return await client.post(
            LOGIN_USER_URL,
            json={
                "user": settings.ROCKETCHAT_USER,
                "password": settings.ROCKETCHAT_PASSWORD,
            },
        )
