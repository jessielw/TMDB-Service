-- Collections
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_collections') THEN
    ALTER TABLE movie_collections RENAME TO movie_collections_old;
END IF;
    ALTER TABLE staging_movie_collections RENAME TO movie_collections;
END
$$;

-- Genres
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_genres') THEN
    ALTER TABLE movie_genres RENAME TO movie_genres_old;
END IF;
    ALTER TABLE staging_movie_genres RENAME TO movie_genres;
END
$$;

-- Genres Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_genres_assoc') THEN
    ALTER TABLE movie_genres_assoc RENAME TO movie_genres_assoc_old;
END IF;
    ALTER TABLE staging_movie_genres_assoc RENAME TO movie_genres_assoc;
END
$$;

-- Production Companies
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_production_companies') THEN
    ALTER TABLE movie_production_companies RENAME TO movie_production_companies_old;
END IF;
    ALTER TABLE staging_movie_production_companies RENAME TO movie_production_companies;
END
$$;

-- Companies Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_companies_assoc') THEN
    ALTER TABLE movie_companies_assoc RENAME TO movie_companies_assoc_old;
END IF;
    ALTER TABLE staging_movie_companies_assoc RENAME TO movie_companies_assoc;
END
$$;

-- Production Countries
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_production_countries') THEN
    ALTER TABLE movie_production_countries RENAME TO movie_production_countries_old;
END IF;
    ALTER TABLE staging_movie_production_countries RENAME TO movie_production_countries;
END
$$;

-- Countries Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_countries_assoc') THEN
    ALTER TABLE movie_countries_assoc RENAME TO movie_countries_assoc_old;
END IF;
    ALTER TABLE staging_movie_countries_assoc RENAME TO movie_countries_assoc;
END
$$;

-- Spoken Languages
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_spoken_languages') THEN
    ALTER TABLE movie_spoken_languages RENAME TO movie_spoken_languages_old;
END IF;
    ALTER TABLE staging_movie_spoken_languages RENAME TO movie_spoken_languages;
END
$$;

-- Languages Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_languages_assoc') THEN
    ALTER TABLE movie_languages_assoc RENAME TO movie_languages_assoc_old;
END IF;
    ALTER TABLE staging_movie_languages_assoc RENAME TO movie_languages_assoc;
END
$$;

-- Alternative Titles
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_alternative_titles') THEN
    ALTER TABLE movie_alternative_titles RENAME TO movie_alternative_titles_old;
END IF;
    ALTER TABLE staging_movie_alternative_titles RENAME TO movie_alternative_titles;
END
$$;

-- Cast Members
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_cast_members') THEN
    ALTER TABLE movie_cast_members RENAME TO movie_cast_members_old;
END IF;
    ALTER TABLE staging_movie_cast_members RENAME TO movie_cast_members;
END
$$;

-- Cast Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_cast_assoc') THEN
    ALTER TABLE movie_cast_assoc RENAME TO movie_cast_assoc_old;
END IF;
    ALTER TABLE staging_movie_cast_assoc RENAME TO movie_cast_assoc;
END
$$;

-- External IDs
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_external_ids') THEN
    ALTER TABLE movie_external_ids RENAME TO movie_external_ids_old;
END IF;
    ALTER TABLE staging_movie_external_ids RENAME TO movie_external_ids;
END
$$;

-- Keywords
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_keywords') THEN
    ALTER TABLE movie_keywords RENAME TO movie_keywords_old;
END IF;
    ALTER TABLE staging_movie_keywords RENAME TO movie_keywords;
END
$$;

-- Keywords Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_keywords_assoc') THEN
    ALTER TABLE movie_keywords_assoc RENAME TO movie_keywords_assoc_old;
END IF;
    ALTER TABLE staging_movie_keywords_assoc RENAME TO movie_keywords_assoc;
END
$$;

-- Release Dates
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_release_dates') THEN
    ALTER TABLE movie_release_dates RENAME TO movie_release_dates_old;
END IF;
    ALTER TABLE staging_movie_release_dates RENAME TO movie_release_dates;
END
$$;

-- Videos
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie_videos') THEN
    ALTER TABLE movie_videos RENAME TO movie_videos_old;
END IF;
    ALTER TABLE staging_movie_videos RENAME TO movie_videos;
END
$$;

-- Movie
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'movie') THEN
    ALTER TABLE movie RENAME TO movie_old;
END IF;
    ALTER TABLE staging_movie RENAME TO movie;
END
$$;

