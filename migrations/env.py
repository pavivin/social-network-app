from alembic import context
from sqlalchemy import create_engine

from voices.config import settings
from voices.db import Base

config = context.config

from voices.app.auth.models import *  # noqa


def run_migrations_online() -> None:
    engine = create_engine(settings.ALEMBIC_DATABASE_URL)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
