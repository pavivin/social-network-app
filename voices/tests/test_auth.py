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
    response = client.post("/api/login", json=data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register(session: AsyncSession, client: AsyncClient):
    data = {"email": "string", "password": "password"}
    response = client.post("/api/registration", json=data)
    assert response.status_code == 200
    query = select(func.count(User.id))
    result = (await session.execute(query)).scalars().first()
    assert result == 1
