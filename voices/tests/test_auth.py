import pytest
import pytest_asyncio
from factories import UserFactory
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from voices.app.auth.models import User


@pytest_asyncio.fixture
async def user():
    user = await UserFactory.create()
    return user


@pytest.mark.asyncio
async def test_login(user: User, client: AsyncClient):
    data = {"email": user.email, "password": "password"}
    response = await client.post("/api/login", json=data)
    assert response.json()["code"] == 200


@pytest.mark.asyncio
async def test_register(session: AsyncSession, client: AsyncClient):
    query = select(func.count(User.id))

    result = (await session.execute(query)).scalars().first()
    assert result == 0

    data = {"email": "string@string.ru", "password": "password"}
    response = await client.post("/api/registration", json=data)
    assert response.json()["code"] == 200

    result = (await session.execute(query)).scalars().first()
    assert result == 1
