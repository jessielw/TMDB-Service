import logging
import os
import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool

from tmdb_service.db_utils import Base
from tmdb_service.models import (  # noqa: F401
    job_queue,
    movies,
    series,
    service_metadata,
)

BASELINE_REVISION = "0001_pre_alembic_1_1"
MIGRATION_LOCK_ID = 1414341698
DATABASE_ATTEMPTS = 30
DATABASE_RETRY_SECONDS = 2

logger = logging.getLogger("tmdb.migrations")


def _alembic_config(connection) -> Config:
    config = Config()
    config.set_main_option(
        "script_location", str(Path(__file__).with_name("migrations"))
    )
    config.attributes["connection"] = connection
    return config


def _bootstrap_unversioned_database(connection, config: Config) -> None:
    tables = set(inspect(connection).get_table_names())
    if "alembic_version" in tables:
        return

    expected = set(Base.metadata.tables)
    existing_managed = tables & expected
    if not existing_managed:
        logger.info("Empty database detected; applying migrations from base.")
        return

    required_existing = expected - {"job_queue"}
    missing = required_existing - tables
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise RuntimeError(
            "Refusing to stamp an unversioned partial or unknown TMDB schema. "
            f"Missing expected tables: {missing_list}."
        )

    logger.info("Recognized an unversioned TMDB schema; stamping the 1.1 baseline.")
    command.stamp(config, BASELINE_REVISION)


def _connect_with_retry(engine: Engine) -> Connection:
    for attempt in range(1, DATABASE_ATTEMPTS):
        try:
            return engine.connect()
        except OperationalError:
            logger.warning(
                "Database is not ready; retrying migration connection (%s/%s).",
                attempt,
                DATABASE_ATTEMPTS,
            )
            time.sleep(DATABASE_RETRY_SECONDS)

    return engine.connect()


def run_migrations() -> None:
    database_uri = os.environ["DATABASE_URI"].strip()
    engine = create_engine(database_uri, poolclass=NullPool)
    connection = _connect_with_retry(engine)
    try:
        connection.execute(
            text("SELECT pg_advisory_lock(:lock_id)"),
            {"lock_id": MIGRATION_LOCK_ID},
        )
        connection.commit()
        try:
            config = _alembic_config(connection)
            _bootstrap_unversioned_database(connection, config)
            command.upgrade(config, "head")
            connection.commit()
            logger.info("Database schema is at the Alembic head revision.")
        except Exception:
            if connection.in_transaction():
                connection.rollback()
            raise
        finally:
            if connection.in_transaction():
                connection.rollback()
            connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": MIGRATION_LOCK_ID},
            )
            connection.commit()
    finally:
        connection.close()
        engine.dispose()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    run_migrations()


if __name__ == "__main__":
    main()
