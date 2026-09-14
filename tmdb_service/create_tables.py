from sqlalchemy import text

from tmdb_service.globals import Base, db
from tmdb_service.models import movies, series, service_metadata  # noqa: F401

CAST_ROLE_MIGRATION_SQL = """
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


def create_tables():
    # get the engine from sessionmaker (db)
    engine = db.kw["bind"]
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text(CAST_ROLE_MIGRATION_SQL))


if __name__ == "__main__":
    create_tables()
