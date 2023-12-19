import uuid

import httpx
from async_lru import alru_cache
from voices.config import settings

ALL_USER_URL = settings.ROCKETCHAT_URL + "/api/v1/users.list"
CREATE_USER_URL = settings.ROCKETCHAT_URL + "/api/v1/users.create"
DELETE_USER_URL = settings.ROCKETCHAT_URL + "/api/v1/users.delete"
LOGIN_USER_URL = settings.ROCKETCHAT_URL + "/api/v1/login"
PUSH_CREATE_URL = settings.ROCKETCHAT_URL + "/api/v1/push.token"

APP_NAME = "startup.cifra.voices_mobile"


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


async def create_gcm_token(token: str):
    async with httpx.AsyncClient() as client:
        return await client.post(
            PUSH_CREATE_URL,
            json={
                "type": "gcm",
                "value": token,
                "appName": APP_NAME,
            },
        )


async def get_users():
    response = await __login_superuser()
    json_response = response.json()
    superuser_id = json_response["data"]["userId"]
    superuser_auth_token = json_response["data"]["authToken"]

    async with httpx.AsyncClient() as client:
        return await client.get(
            ALL_USER_URL,
            headers={
                "X-Auth-Token": superuser_auth_token,
                "X-User-Id": superuser_id,
            },
        )


async def delete_user(user_id: str):
    response = await __login_superuser()
    json_response = response.json()
    superuser_id = json_response["data"]["userId"]
    superuser_auth_token = json_response["data"]["authToken"]

    async with httpx.AsyncClient() as client:
        return await client.post(
            DELETE_USER_URL,
            json={
                "user": user_id,
            },
            headers={
                "X-Auth-Token": superuser_auth_token,
                "X-User-Id": superuser_id,
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
