-- The replaced production tables (and their canonical indexes) have been
-- dropped by this point. Give the promoted staging indexes their stable names.
ALTER INDEX ix_staging_movie_tmdb_search_title
    RENAME TO ix_movie_tmdb_search_title;

ALTER INDEX ix_staging_series_tmdb_search_name
    RENAME TO ix_series_tmdb_search_name;
