from alembic import context
from sqlalchemy import create_engine

# TODO: autoupload all files with names models
from voices.app.auth.models import *  # noqa
from voices.app.friends.models import *  # noqa
from voices.app.initiatives.models import *  # noqa
from voices.app.notifications.models import *  # noqa
from voices.config import settings
from voices.db import Base

config = context.config

IGNORE_TABLES = {
    "spatial_ref_sys",
    "django_admin_log",
    "auth_user",
    "auth_permission",
    "django_session",
    "django_migrations",
    "auth_group_permissions",
    "django_content_type",
    "auth_user_user_permissions",
    "auth_user_groups",
    "auth_group",
}


def include_object(object, name, type_, reflected, compare_to):
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
