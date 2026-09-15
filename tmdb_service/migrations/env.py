import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from tmdb_service.db_utils import Base
from tmdb_service.models import (  # noqa: F401
    job_queue,
    movies,
    series,
    service_metadata,
)

config = context.config
target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    if type_ != "table" or name is None:
        return True
    return not (name.startswith("staging_") or name.endswith("_old"))


def configure_context(connection=None, url=None):
    context.configure(
        connection=connection,
        url=url,
        target_metadata=target_metadata,
        include_name=include_name,
        compare_type=True,
        compare_server_default=True,
    )


def run_migrations_offline() -> None:
    configure_context(url=os.environ["DATABASE_URI"])
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    supplied_connection = config.attributes.get("connection")
    if supplied_connection is not None:
        configure_context(connection=supplied_connection)
        with context.begin_transaction():
            context.run_migrations()
        return

    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = os.environ["DATABASE_URI"]
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        configure_context(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
