from contextvars import ContextVar
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from voices.db.base import container

db_session: ContextVar[AsyncSession] = ContextVar("db_session", default=None)


def auto_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = db_session.get()
        return_value = func(session=session, *args, **kwargs)
        return return_value

    return wrapper


class Transaction:
    async def __aenter__(self):
        session_maker = container.resolve(sessionmaker)
        self.session: AsyncSession = session_maker()
        self.token = db_session.set(self.session)
        return self

    async def __aexit__(self, exception_type, exception, traceback):
        if exception:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
        db_session.reset(self.token)
