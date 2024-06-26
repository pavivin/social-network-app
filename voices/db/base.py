import punq
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from voices.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)

Base = declarative_base()
session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


test_engine = create_async_engine(settings.TEST_DATABASE_URL, echo=True)

session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
test_session_maker = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
sc_session = scoped_session(test_session_maker)


class SessionMaker:
    def __new__(cls):
        return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class TestSessionMaker:
    def __new__(cls):
        return sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


container = punq.Container()
container.register(sessionmaker, SessionMaker)
