"""Upgrade the pre-Alembic schema to the 1.2 schema.

Revision ID: 0002_v1_2_schema
Revises: 0001_pre_alembic_1_1
"""

from alembic import op
from sqlalchemy import inspect

revision = "0002_v1_2_schema"
down_revision = "0001_pre_alembic_1_1"
branch_labels = None
depends_on = None


CAST_ROLE_SQL = """
ALTER TABLE movie_cast_assoc ADD COLUMN IF NOT EXISTS character TEXT;
ALTER TABLE movie_cast_assoc ADD COLUMN IF NOT EXISTS cast_order SMALLINT;
ALTER TABLE series_cast_assoc ADD COLUMN IF NOT EXISTS character TEXT;
ALTER TABLE series_cast_assoc ADD COLUMN IF NOT EXISTS cast_order SMALLINT;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'movie_cast_members'
          AND column_name = 'character'
    ) THEN
        UPDATE movie_cast_assoc AS role
        SET character = member.character,
            cast_order = member.cast_order
        FROM movie_cast_members AS member
        WHERE role.cast_id = member.id;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'series_cast_members'
          AND column_name = 'character'
    ) THEN
        UPDATE series_cast_assoc AS role
        SET character = member.character,
            cast_order = member.cast_order
        FROM series_cast_members AS member
        WHERE role.cast_id = member.id;
    END IF;
END
$$;

ALTER TABLE movie_cast_members DROP COLUMN IF EXISTS character;
ALTER TABLE movie_cast_members DROP COLUMN IF EXISTS cast_order;
ALTER TABLE series_cast_members DROP COLUMN IF EXISTS character;
ALTER TABLE series_cast_members DROP COLUMN IF EXISTS cast_order;
"""


JOB_QUEUE_SQL = """
CREATE TABLE IF NOT EXISTS job_queue (
    id SERIAL PRIMARY KEY,
    job_type TEXT NOT NULL,
    payload TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    last_error TEXT
);

ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'queued';
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ;
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS last_error TEXT;

UPDATE job_queue SET created_at = now() WHERE created_at IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'job_queue'
          AND data_type = 'timestamp without time zone'
          AND column_name = 'created_at'
    ) THEN
        ALTER TABLE job_queue
            ALTER COLUMN created_at TYPE TIMESTAMPTZ
            USING created_at AT TIME ZONE 'UTC';
    END IF;
END
$$;

ALTER TABLE job_queue
    ALTER COLUMN created_at SET DEFAULT now(),
    ALTER COLUMN created_at SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'job_queue_status_check'
          AND conrelid = 'job_queue'::regclass
    ) THEN
        ALTER TABLE job_queue
            ADD CONSTRAINT job_queue_status_check
            CHECK (status IN ('queued', 'running', 'failed'));
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS job_queue_status_created_idx
    ON job_queue (status, created_at, id);

CREATE OR REPLACE FUNCTION notify_new_job() RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify('new_job', NEW.id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS job_insert_notify ON job_queue;
CREATE TRIGGER job_insert_notify
AFTER INSERT ON job_queue
FOR EACH ROW EXECUTE FUNCTION notify_new_job();
"""


# table, local columns, referred table, referred columns, on-delete, deferred
FOREIGN_KEYS = (
    ("movie", ("belongs_to_collection_id",), "movie_collections", ("id",), None, False),
    ("movie_genres_assoc", ("movie_id",), "movie", ("id",), "CASCADE", False),
    ("movie_genres_assoc", ("genre_id",), "movie_genres", ("id",), "CASCADE", False),
    ("movie_companies_assoc", ("movie_id",), "movie", ("id",), "CASCADE", False),
    (
        "movie_companies_assoc",
        ("company_id",),
        "movie_production_companies",
        ("id",),
        "CASCADE",
        False,
    ),
    ("movie_countries_assoc", ("movie_id",), "movie", ("id",), "CASCADE", False),
    (
        "movie_countries_assoc",
        ("country_id",),
        "movie_production_countries",
        ("iso_3166_1",),
        "CASCADE",
        False,
    ),
    ("movie_languages_assoc", ("movie_id",), "movie", ("id",), "CASCADE", False),
    (
        "movie_languages_assoc",
        ("language_id",),
        "movie_spoken_languages",
        ("iso_639_1",),
        "CASCADE",
        False,
    ),
    ("movie_alternative_titles", ("movie_id",), "movie", ("id",), "CASCADE", False),
    ("movie_cast_assoc", ("movie_id",), "movie", ("id",), "CASCADE", False),
    ("movie_cast_assoc", ("cast_id",), "movie_cast_members", ("id",), "CASCADE", False),
    ("movie_external_ids", ("movie_id",), "movie", ("id",), "CASCADE", False),
    ("movie_keywords_assoc", ("movie_id",), "movie", ("id",), "CASCADE", False),
    ("movie_keywords_assoc", ("id",), "movie_keywords", ("id",), "CASCADE", False),
    ("movie_release_dates", ("movie_id",), "movie", ("id",), "CASCADE", False),
    ("movie_videos", ("movie_id",), "movie", ("id",), "CASCADE", False),
    (
        "series",
        ("last_episode_to_air_id",),
        "series_last_episode_to_air",
        ("id",),
        None,
        True,
    ),
    (
        "series",
        ("next_episode_to_air_id",),
        "series_next_episode_to_air",
        ("id",),
        None,
        True,
    ),
    ("series_created_by_assoc", ("series_id",), "series", ("id",), "CASCADE", False),
    (
        "series_created_by_assoc",
        ("created_by_id",),
        "series_created_by",
        ("id",),
        "CASCADE",
        False,
    ),
    ("series_genres_assoc", ("series_id",), "series", ("id",), "CASCADE", False),
    ("series_genres_assoc", ("genre_id",), "series_genres", ("id",), "CASCADE", False),
    ("series_networks_assoc", ("series_id",), "series", ("id",), "CASCADE", False),
    (
        "series_networks_assoc",
        ("network_id",),
        "series_networks",
        ("id",),
        "CASCADE",
        False,
    ),
    ("series_companies_assoc", ("series_id",), "series", ("id",), "CASCADE", False),
    (
        "series_companies_assoc",
        ("company_id",),
        "series_production_companies",
        ("id",),
        "CASCADE",
        False,
    ),
    ("series_countries_assoc", ("series_id",), "series", ("id",), "CASCADE", False),
    (
        "series_countries_assoc",
        ("country_id",),
        "series_production_countries",
        ("iso_3166_1",),
        "CASCADE",
        False,
    ),
    ("series_seasons", ("series_id",), "series", ("id",), "CASCADE", False),
    ("series_languages_assoc", ("series_id",), "series", ("id",), "CASCADE", False),
    (
        "series_languages_assoc",
        ("language_id",),
        "series_spoken_languages",
        ("iso_639_1",),
        "CASCADE",
        False,
    ),
    ("series_alternative_titles", ("series_id",), "series", ("id",), "CASCADE", False),
    ("series_cast_assoc", ("series_id",), "series", ("id",), "CASCADE", False),
    (
        "series_cast_assoc",
        ("cast_id",),
        "series_cast_members",
        ("id",),
        "CASCADE",
        False,
    ),
    ("series_external_ids", ("series_id",), "series", ("id",), "CASCADE", False),
    ("series_keywords_assoc", ("series_id",), "series", ("id",), "CASCADE", False),
    ("series_keywords_assoc", ("id",), "series_keywords", ("id",), "CASCADE", False),
    ("series_videos", ("series_id",), "series", ("id",), "CASCADE", False),
)


def _ensure_foreign_key(
    table_name,
    columns,
    referred_table,
    referred_columns,
    ondelete,
    deferred,
) -> None:
    expected_name = f"fk_{table_name}_{columns[0]}"
    existing = [
        foreign_key
        for foreign_key in inspect(op.get_bind()).get_foreign_keys(table_name)
        if tuple(foreign_key["constrained_columns"]) == columns
    ]

    for foreign_key in existing:
        options = foreign_key.get("options") or {}
        matches = (
            foreign_key["name"] == expected_name
            and foreign_key["referred_table"] == referred_table
            and tuple(foreign_key["referred_columns"]) == referred_columns
            and options.get("ondelete") == ondelete
            and bool(options.get("deferrable")) == deferred
            and (not deferred or options.get("initially", "").upper() == "DEFERRED")
        )
        if matches and len(existing) == 1:
            return

    for foreign_key in existing:
        op.drop_constraint(foreign_key["name"], table_name, type_="foreignkey")

    op.create_foreign_key(
        expected_name,
        table_name,
        referred_table,
        list(columns),
        list(referred_columns),
        ondelete=ondelete,
        deferrable=True if deferred else None,
        initially="DEFERRED" if deferred else None,
        # Legacy full sweeps could leave dangling relationship rows. Preserve
        # them during the first Alembic adoption while enforcing the key for
        # every new write. A subsequent staging-table full sweep installs the
        # same constraints fully validated against its clean replacement data.
        postgresql_not_valid=True,
    )


def upgrade() -> None:
    op.execute(CAST_ROLE_SQL)
    op.execute(JOB_QUEUE_SQL)
    for foreign_key in FOREIGN_KEYS:
        _ensure_foreign_key(*foreign_key)


def downgrade() -> None:
    raise RuntimeError(
        "The 1.2 cast-role migration is forward-only; restore a backup to roll back."
    )
