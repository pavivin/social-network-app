from alembic import context
from sqlalchemy import create_engine

from voices.config import settings
from voices.db import Base

config = context.config

from voices.app.auth.models import *  # noqa
from voices.app.comments.models import *  # noqa
from voices.app.initiatives.models import *  # noqa
from voices.app.likes.models import *  # noqa

IGNORE_TABLES = ("spatial_ref_sys",)


def include_object(object, name, type_, reflected, compare_to):
    """
    Should you include this table or not?
    """

    if type_ == "table" and (name in IGNORE_TABLES or object.info.get("skip_autogenerate", False)):
        return False

    elif type_ == "column" and object.info.get("skip_autogenerate", False):
        return False

    return True


def run_migrations_online() -> None:
    engine = create_engine(settings.ALEMBIC_DATABASE_URL)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
