-- Created By
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_created_by') THEN
    ALTER TABLE series_created_by RENAME TO series_created_by_old;
END IF;
    ALTER TABLE staging_series_created_by RENAME TO series_created_by;
END
$$;

-- Created By Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_created_by_assoc') THEN
    ALTER TABLE series_created_by_assoc RENAME TO series_created_by_assoc_old;
END IF;
    ALTER TABLE staging_series_created_by_assoc RENAME TO series_created_by_assoc;
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
            table_name = 'series_genres') THEN
    ALTER TABLE series_genres RENAME TO series_genres_old;
END IF;
    ALTER TABLE staging_series_genres RENAME TO series_genres;
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
            table_name = 'series_genres_assoc') THEN
    ALTER TABLE series_genres_assoc RENAME TO series_genres_assoc_old;
END IF;
    ALTER TABLE staging_series_genres_assoc RENAME TO series_genres_assoc;
END
$$;

-- Last Episode to Air
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_last_episode_to_air') THEN
    ALTER TABLE series_last_episode_to_air RENAME TO series_last_episode_to_air_old;
END IF;
    ALTER TABLE staging_series_last_episode_to_air RENAME TO series_last_episode_to_air;
END
$$;

-- Next Episode to Air
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_next_episode_to_air') THEN
    ALTER TABLE series_next_episode_to_air RENAME TO series_next_episode_to_air_old;
END IF;
    ALTER TABLE staging_series_next_episode_to_air RENAME TO series_next_episode_to_air;
END
$$;

-- Networks
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_networks') THEN
    ALTER TABLE series_networks RENAME TO series_networks_old;
END IF;
    ALTER TABLE staging_series_networks RENAME TO series_networks;
END
$$;

-- Networks Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_networks_assoc') THEN
    ALTER TABLE series_networks_assoc RENAME TO series_networks_assoc_old;
END IF;
    ALTER TABLE staging_series_networks_assoc RENAME TO series_networks_assoc;
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
            table_name = 'series_production_companies') THEN
    ALTER TABLE series_production_companies RENAME TO series_production_companies_old;
END IF;
    ALTER TABLE staging_series_production_companies RENAME TO series_production_companies;
END
$$;

-- Production Companies Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_companies_assoc') THEN
    ALTER TABLE series_companies_assoc RENAME TO series_companies_assoc_old;
END IF;
    ALTER TABLE staging_series_companies_assoc RENAME TO series_companies_assoc;
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
            table_name = 'series_production_countries') THEN
    ALTER TABLE series_production_countries RENAME TO series_production_countries_old;
END IF;
    ALTER TABLE staging_series_production_countries RENAME TO series_production_countries;
END
$$;

-- Production Countries Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_countries_assoc') THEN
    ALTER TABLE series_countries_assoc RENAME TO series_countries_assoc_old;
END IF;
    ALTER TABLE staging_series_countries_assoc RENAME TO series_countries_assoc;
END
$$;

-- Seasons
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_seasons') THEN
    ALTER TABLE series_seasons RENAME TO series_seasons_old;
END IF;
    ALTER TABLE staging_series_seasons RENAME TO series_seasons;
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
            table_name = 'series_spoken_languages') THEN
    ALTER TABLE series_spoken_languages RENAME TO series_spoken_languages_old;
END IF;
    ALTER TABLE staging_series_spoken_languages RENAME TO series_spoken_languages;
END
$$;

-- Spoken Languages Associations
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_languages_assoc') THEN
    ALTER TABLE series_languages_assoc RENAME TO series_languages_assoc_old;
END IF;
    ALTER TABLE staging_series_languages_assoc RENAME TO series_languages_assoc;
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
            table_name = 'series_alternative_titles') THEN
    ALTER TABLE series_alternative_titles RENAME TO series_alternative_titles_old;
END IF;
    ALTER TABLE staging_series_alternative_titles RENAME TO series_alternative_titles;
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
            table_name = 'series_cast_members') THEN
    ALTER TABLE series_cast_members RENAME TO series_cast_members_old;
END IF;
    ALTER TABLE staging_series_cast_members RENAME TO series_cast_members;
END
$$;

-- Cast Members Association
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series_cast_assoc') THEN
    ALTER TABLE series_cast_assoc RENAME TO series_cast_assoc_old;
END IF;
    ALTER TABLE staging_series_cast_assoc RENAME TO series_cast_assoc;
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
            table_name = 'series_external_ids') THEN
    ALTER TABLE series_external_ids RENAME TO series_external_ids_old;
END IF;
    ALTER TABLE staging_series_external_ids RENAME TO series_external_ids;
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
            table_name = 'series_keywords') THEN
    ALTER TABLE series_keywords RENAME TO series_keywords_old;
END IF;
    ALTER TABLE staging_series_keywords RENAME TO series_keywords;
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
            table_name = 'series_keywords_assoc') THEN
    ALTER TABLE series_keywords_assoc RENAME TO series_keywords_assoc_old;
END IF;
    ALTER TABLE staging_series_keywords_assoc RENAME TO series_keywords_assoc;
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
            table_name = 'series_videos') THEN
    ALTER TABLE series_videos RENAME TO series_videos_old;
END IF;
    ALTER TABLE staging_series_videos RENAME TO series_videos;
END
$$;

-- Series
DO $$
BEGIN
    IF EXISTS(
        SELECT
            1
        FROM
            information_schema.tables
        WHERE
            table_name = 'series') THEN
    ALTER TABLE series RENAME TO series_old;
END IF;
    ALTER TABLE staging_series RENAME TO series;
END
$$;

