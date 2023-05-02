from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession

from vizme.db.base import session_maker

db_session: ContextVar[AsyncSession] = ContextVar("db_session", default=None)
# TODO: pass automaticly in all db functions


class Transaction:
    async def __aenter__(self):
        self.session = session_maker()
        self.token = db_session.set(self.session)

    async def __aexit__(self, exception_type, exception, traceback):
        if exception:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
        db_session.reset(self.token)
