import inspect
import sys
from asyncio import get_event_loop_policy

import pytest
import pytest_asyncio
from factory.base import FactoryMetaClass
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from main import app
from vizme.config import settings
from vizme.db import Base


@pytest.fixture(scope="session")
def event_loop():
    policy = get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# Replaces db connection with a connection to the test db
engine = create_async_engine(
    settings.TEST_DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
)


@pytest_asyncio.fixture
async def prepare_db():
    # Clears previous tables in db and creates new ones
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
        yield


@pytest_asyncio.fixture
async def async_session(prepare_db) -> AsyncSession:
    session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session


@pytest.fixture(autouse=True)
def init_factories(async_session: AsyncSession) -> None:
    """Register session in all factories"""

    for _, instance_class in inspect.getmembers(sys.modules["factories"], inspect.isclass):
        if isinstance(instance_class, FactoryMetaClass):
            instance_class._meta.sqlalchemy_session = async_session


@pytest.fixture
def client() -> AsyncClient:
    yield AsyncClient(app=app, base_url="http://test")
