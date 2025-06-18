-- Created By
DROP TABLE IF EXISTS staging_series_created_by CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_created_by(
    id bigint PRIMARY KEY,
    credit_id varchar(255),
    name text,
    original_name text,
    gender smallint,
    profile_path varchar(255)
);

-- Created By Association
DROP TABLE IF EXISTS staging_series_created_by_assoc CASCADE;

CREATE TABLE staging_series_created_by_assoc(
    series_id bigint,
    created_by_id bigint,
    PRIMARY KEY (series_id, created_by_id)
);

-- Genres
DROP TABLE IF EXISTS staging_series_genres CASCADE;

CREATE TABLE staging_series_genres(
    id bigint PRIMARY KEY,
    name varchar(255)
);

-- Genres Association
DROP TABLE IF EXISTS staging_series_genres_assoc CASCADE;

CREATE TABLE staging_series_genres_assoc(
    series_id bigint,
    genre_id bigint,
    PRIMARY KEY (series_id, genre_id)
);

-- Last Episode to Air
DROP TABLE IF EXISTS staging_series_last_episode_to_air CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_last_episode_to_air(
    id bigint PRIMARY KEY,
    name text,
    overview text,
    vote_average float,
    vote_count bigint,
    air_date timestamp,
    episode_number int,
    episode_type text,
    production_code text,
    runtime int,
    season_number int,
    show_id bigint,
    still_path varchar(255)
);

-- Next Episode to Air
DROP TABLE IF EXISTS staging_series_next_episode_to_air CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_next_episode_to_air(
    id bigint PRIMARY KEY,
    name text,
    overview text,
    vote_average float,
    vote_count bigint,
    air_date timestamp,
    episode_number int,
    episode_type text,
    production_code text,
    runtime int,
    season_number int,
    show_id bigint,
    still_path varchar(255)
);

-- Networks
DROP TABLE IF EXISTS staging_series_networks CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_networks(
    id bigint PRIMARY KEY,
    logo_path varchar(255),
    name text,
    origin_country varchar(64)
);

-- Networks Association
DROP TABLE IF EXISTS staging_series_networks_assoc CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_networks_assoc(
    series_id bigint,
    network_id bigint,
    PRIMARY KEY (series_id, network_id)
);

-- Production Companies
DROP TABLE IF EXISTS staging_series_production_companies CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_production_companies(
    id bigint PRIMARY KEY,
    name text,
    origin_country varchar(255),
    logo_path varchar(255)
);

-- Production Companies Association
DROP TABLE IF EXISTS staging_series_companies_assoc CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_companies_assoc(
    series_id bigint,
    company_id bigint,
    PRIMARY KEY (series_id, company_id)
);

-- Production Countries
DROP TABLE IF EXISTS staging_series_production_countries CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_production_countries(
    iso_3166_1 text PRIMARY KEY,
    name text
);

-- Production Countries Association
DROP TABLE IF EXISTS staging_series_countries_assoc CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_countries_assoc(
    series_id bigint,
    country_id text,
    PRIMARY KEY (series_id, country_id)
);

-- Seasons
DROP TABLE IF EXISTS staging_series_seasons CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_seasons(
    id bigint PRIMARY KEY,
    air_date timestamp,
    episode_count int,
    name text,
    overview text,
    poster_path varchar(255),
    season_number int,
    vote_average float,
    series_id bigint
);

-- Spoken Languages
DROP TABLE IF EXISTS staging_series_spoken_languages CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_spoken_languages(
    iso_639_1 text PRIMARY KEY,
    english_name varchar(255),
    name varchar(255)
);

-- Spoken Languages Association
DROP TABLE IF EXISTS staging_series_languages_assoc CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_languages_assoc(
    series_id bigint,
    language_id text,
    PRIMARY KEY (series_id, language_id)
);

-- Alternative Titles
DROP TABLE IF EXISTS staging_series_alternative_titles CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_alternative_titles(
    id bigserial PRIMARY KEY,
    iso_3166_1 text,
    title text,
    type text,
    series_id bigint
);

-- Cast
DROP TABLE IF EXISTS staging_series_cast_members CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_cast_members(
    id bigint PRIMARY KEY,
    adult boolean,
    gender smallint,
    cast_id bigint,
    name varchar(255),
    original_name varchar(255),
    known_for_department varchar(255),
    popularity float,
    profile_path varchar(255),
    character text,
    cast_order smallint
);

-- Cast Association
DROP TABLE IF EXISTS staging_series_cast_assoc CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_cast_assoc(
    series_id bigint,
    cast_id bigint,
    PRIMARY KEY (series_id, cast_id)
);

-- External IDs
DROP TABLE IF EXISTS staging_series_external_ids CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_external_ids(
    series_id bigint PRIMARY KEY,
    imdb_id varchar(255),
    wikidata_id varchar(255),
    facebook_id varchar(255),
    instagram_id varchar(255),
    twitter_id varchar(255)
);

-- Keywords
DROP TABLE IF EXISTS staging_series_keywords CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_keywords(
    id bigint PRIMARY KEY,
    name varchar(255)
);

-- Keywords Association
DROP TABLE IF EXISTS staging_series_keywords_assoc CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_keywords_assoc(
    series_id bigint,
    id bigint,
    PRIMARY KEY (series_id, id)
);

-- Videos
DROP TABLE IF EXISTS staging_series_videos CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_videos(
    id varchar(255) PRIMARY KEY,
    iso_639_1 text,
    iso_3166_1 text,
    name text,
    key varchar(255),
    site varchar(255),
    size int,
    type varchar(255),
    official boolean,
    published_at timestamp,
    series_id bigint
);

-- Series
DROP TABLE IF EXISTS staging_series CASCADE;

CREATE TABLE IF NOT EXISTS staging_series(
    id bigint PRIMARY KEY,
    backdrop_path varchar(255),
    first_air_date timestamp,
    homepage text,
    imdb_id varchar(12),
    in_production boolean,
    last_air_date timestamp,
    name text,
    number_of_episodes int,
    number_of_seasons int,
    origin_country text,
    original_language varchar(64),
    original_name text,
    overview text,
    popularity float,
    poster_path varchar(255),
    status text,
    tagline text,
    type TEXT,
    vote_average float,
    vote_count bigint,
    last_episode_to_air_id bigint,
    next_episode_to_air_id bigint
);

