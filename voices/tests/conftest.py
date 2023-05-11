import inspect
import sys
from asyncio import get_event_loop_policy

import pytest
import pytest_asyncio
from factory.base import FactoryMetaClass
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app
from voices.db import Base
from voices.db.base import TestSessionMaker, container, test_engine, test_session_maker


@pytest.fixture(scope="session")
def event_loop():
    policy = get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def prepare_db():
    # Clears previous tables in db and creates new ones
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
        yield


@pytest_asyncio.fixture
async def session(prepare_db) -> AsyncSession:
    async with test_session_maker() as session:
        yield session


@pytest.fixture(autouse=True)
def init_factories(session: AsyncSession) -> None:
    """Register session in all factories"""

    for _, instance_class in inspect.getmembers(sys.modules["factories"], inspect.isclass):
        if isinstance(instance_class, FactoryMetaClass):
            instance_class._meta.sqlalchemy_session = session


@pytest.fixture
def client() -> AsyncClient:
    container.register(sessionmaker, TestSessionMaker)
    yield AsyncClient(app=app, base_url="http://test")
