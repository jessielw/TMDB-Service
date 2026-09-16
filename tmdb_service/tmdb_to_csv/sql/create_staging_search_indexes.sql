-- Build search indexes before promotion so the production table is never
-- left unindexed after a full sweep. Temporary names avoid colliding with
-- the indexes still attached to the current production tables.
CREATE INDEX ix_staging_movie_tmdb_search_title
    ON staging_movie USING gin
    (tmdb_normalize_title(title) public.gin_trgm_ops);

CREATE INDEX ix_staging_series_tmdb_search_name
    ON staging_series USING gin
    (tmdb_normalize_title(name) public.gin_trgm_ops);

-- COPY does not populate planner statistics. They survive the table rename,
-- so analyze before promotion and make the new tables fast immediately.
ANALYZE staging_movie;
ANALYZE staging_series;
