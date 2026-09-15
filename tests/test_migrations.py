import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from tmdb_service.db_utils import Base
from tmdb_service.migrate import (
    BASELINE_REVISION,
    _alembic_config,
    run_migrations,
)
from tmdb_service.models import (  # noqa: F401
    job_queue,
    movies,
    series,
    service_metadata,
)

TEST_DATABASE_URI = os.environ.get("TMDB_TEST_DATABASE_URI")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URI,
    reason="TMDB_TEST_DATABASE_URI is required for PostgreSQL migration tests",
)


@pytest.fixture
def isolated_database_uri():
    schema = f"tmdb_test_{uuid.uuid4().hex}"
    if not TEST_DATABASE_URI:
        raise RuntimeError("TMDB_TEST_DATABASE_URI is missing")
    admin_engine = create_engine(TEST_DATABASE_URI)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    url = make_url(TEST_DATABASE_URI).update_query_dict(
        {"options": f"-csearch_path={schema}"}
    )
    isolated_uri = url.render_as_string(hide_password=False)
    verification_engine = create_engine(isolated_uri)
    with verification_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT current_schema()")).scalar_one() == schema
        )
    verification_engine.dispose()

    try:
        yield isolated_uri
    finally:
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin_engine.dispose()


def migrate_uri(monkeypatch, database_uri):
    monkeypatch.setenv("DATABASE_URI", database_uri)
    run_migrations()


def current_revision(database_uri):
    engine = create_engine(database_uri)
    try:
        with engine.connect() as connection:
            return connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
    finally:
        engine.dispose()


def test_empty_database_migrates_to_head_and_is_idempotent(
    monkeypatch, isolated_database_uri
):
    migrate_uri(monkeypatch, isolated_database_uri)
    assert current_revision(isolated_database_uri) == "0002_v1_2_schema"

    engine = create_engine(isolated_database_uri)
    try:
        assert set(Base.metadata.tables) <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    migrate_uri(monkeypatch, isolated_database_uri)
    assert current_revision(isolated_database_uri) == "0002_v1_2_schema"


def test_unversioned_legacy_database_is_adopted_and_preserves_cast_data(
    monkeypatch, isolated_database_uri
):
    engine = create_engine(isolated_database_uri)
    with engine.connect() as connection:
        command.upgrade(_alembic_config(connection), BASELINE_REVISION)
        connection.execute(text("INSERT INTO movie (id, title) VALUES (1, 'Example')"))
        connection.execute(
            text(
                "INSERT INTO movie_cast_members "
                "(id, name, character, cast_order) "
                "VALUES (2, 'Alice', 'Lead', 1)"
            )
        )
        connection.execute(
            text("INSERT INTO movie_cast_assoc (movie_id, cast_id) VALUES (1, 2)")
        )
        connection.execute(
            text("INSERT INTO job_queue (job_type) VALUES ('changes_sync')")
        )
        connection.execute(text("DROP TABLE alembic_version"))
        connection.commit()

    migrate_uri(monkeypatch, isolated_database_uri)

    with engine.connect() as connection:
        role = connection.execute(
            text(
                "SELECT character, cast_order FROM movie_cast_assoc "
                "WHERE movie_id = 1 AND cast_id = 2"
            )
        ).one()
        assert role == ("Lead", 1)
        member_columns = {
            column["name"]
            for column in inspect(connection).get_columns("movie_cast_members")
        }
        assert "character" not in member_columns
        assert "cast_order" not in member_columns

        queue_columns = {
            column["name"]: column
            for column in inspect(connection).get_columns("job_queue")
        }
        assert queue_columns["created_at"]["type"].timezone is True  # type: ignore[reportAttributeAccessIssue]
        assert queue_columns["created_at"]["nullable"] is False
        assert (
            connection.execute(text("SELECT status FROM job_queue")).scalar_one()
            == "queued"
        )
    engine.dispose()


def test_already_current_unversioned_database_is_adopted(
    monkeypatch, isolated_database_uri
):
    migrate_uri(monkeypatch, isolated_database_uri)
    engine = create_engine(isolated_database_uri)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE alembic_version"))
    engine.dispose()

    migrate_uri(monkeypatch, isolated_database_uri)
    assert current_revision(isolated_database_uri) == "0002_v1_2_schema"


def test_partial_schema_is_not_stamped(monkeypatch, isolated_database_uri):
    engine = create_engine(isolated_database_uri)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE movie (id BIGINT PRIMARY KEY)"))
    engine.dispose()

    monkeypatch.setenv("DATABASE_URI", isolated_database_uri)
    with pytest.raises(RuntimeError, match="partial or unknown"):
        run_migrations()

    engine = create_engine(isolated_database_uri)
    try:
        assert "alembic_version" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_simultaneous_migrators_serialize(monkeypatch, isolated_database_uri):
    monkeypatch.setenv("DATABASE_URI", isolated_database_uri)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_migrations) for _ in range(2)]
        for future in futures:
            future.result(timeout=30)
    assert current_revision(isolated_database_uri) == "0002_v1_2_schema"


def test_staging_promotion_matches_alembic_metadata(monkeypatch, isolated_database_uri):
    migrate_uri(monkeypatch, isolated_database_uri)
    sql_dir = Path(__file__).parents[1] / "tmdb_service" / "tmdb_to_csv" / "sql"
    engine = create_engine(isolated_database_uri)
    try:
        for filename in ("create_staging_movie.sql", "create_staging_series.sql"):
            with engine.begin() as connection:
                connection.execute(text((sql_dir / filename).read_text()))

        with engine.begin() as connection:
            for filename in (
                "promote_staging_to_production_movie.sql",
                "promote_staging_to_production_series.sql",
                "drop_old_tables_movie.sql",
                "drop_old_tables_series.sql",
            ):
                connection.execute(text((sql_dir / filename).read_text()))

        with engine.connect() as connection:
            command.check(_alembic_config(connection))
    finally:
        engine.dispose()
