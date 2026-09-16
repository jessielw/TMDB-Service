"""Add normalized trigram indexes for title search.

Revision ID: 0003_title_search_indexes
Revises: 0002_v1_2_schema
"""

from alembic import op

revision = "0003_title_search_indexes"
down_revision = "0002_v1_2_schema"
branch_labels = None
depends_on = None


NORMALIZE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION tmdb_normalize_title(value text)
RETURNS text
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
STRICT
AS $$
    SELECT lower(public.unaccent(translate(value, ':.-_'',!/?()[]{}', '')))
$$
"""


def upgrade() -> None:
    # The service owns these extensions and the immutable wrapper because it
    # owns and periodically replaces the indexed movie/series tables.
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public")
    op.execute(NORMALIZE_FUNCTION_SQL)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_movie_tmdb_search_title "
        "ON movie USING gin "
        "(tmdb_normalize_title(title) public.gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_series_tmdb_search_name "
        "ON series USING gin "
        "(tmdb_normalize_title(name) public.gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_series_tmdb_search_name")
    op.execute("DROP INDEX IF EXISTS ix_movie_tmdb_search_title")
    op.execute("DROP FUNCTION IF EXISTS tmdb_normalize_title(text)")
