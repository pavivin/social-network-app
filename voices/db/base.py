from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from voices.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)

Base = declarative_base()
session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


test_engine = create_async_engine(settings.TEST_DATABASE_URL, echo=True)
test_session_maker = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
