-- Created By
DROP TABLE IF EXISTS staging_series_created_by CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_created_by(
    id bigint PRIMARY KEY,
    credit_id varchar(255),
    name varchar,
    original_name varchar,
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
    name varchar,
    overview varchar,
    vote_average float,
    vote_count bigint,
    air_date timestamp,
    episode_number int,
    episode_type varchar,
    production_code varchar,
    runtime int,
    season_number int,
    show_id int,
    still_path varchar(255)
);

-- Next Episode to Air
DROP TABLE IF EXISTS staging_series_next_episode_to_air CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_next_episode_to_air(
    id bigint PRIMARY KEY,
    name varchar,
    overview varchar,
    vote_average float,
    vote_count bigint,
    air_date timestamp,
    episode_number int,
    episode_type varchar,
    production_code varchar,
    runtime int,
    season_number int,
    show_id int,
    still_path varchar(255)
);

-- Networks
DROP TABLE IF EXISTS staging_series_networks CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_networks(
    id bigint PRIMARY KEY,
    logo_path varchar(255),
    name varchar,
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
    name varchar,
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
    iso_3166_1 varchar PRIMARY KEY,
    name varchar
);

-- Production Countries Association
DROP TABLE IF EXISTS staging_series_countries_assoc CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_countries_assoc(
    series_id bigint,
    country_id varchar,
    PRIMARY KEY (series_id, country_id)
);

-- Seasons
DROP TABLE IF EXISTS staging_series_seasons CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_seasons(
    id bigint PRIMARY KEY,
    air_date timestamp,
    episode_count int,
    name varchar,
    overview varchar,
    poster_path varchar(255),
    season_number int,
    vote_average float,
    series_id bigint
);

-- Spoken Languages
DROP TABLE IF EXISTS staging_series_spoken_languages CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_spoken_languages(
    iso_639_1 varchar PRIMARY KEY,
    english_name varchar(255),
    name varchar(255)
);

-- Spoken Languages Association
DROP TABLE IF EXISTS staging_series_languages_assoc CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_languages_assoc(
    series_id bigint,
    language_id varchar,
    PRIMARY KEY (series_id, language_id)
);

-- Alternative Titles
DROP TABLE IF EXISTS staging_series_alternative_titles CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_alternative_titles(
    id bigserial PRIMARY KEY,
    iso_3166_1 varchar,
    title varchar,
    type varchar,
    series_id bigint
);

-- Cast
DROP TABLE IF EXISTS staging_series_cast_members CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_cast_members(
    id bigint PRIMARY KEY,
    adult boolean,
    gender smallint,
    cast_id int,
    name varchar(255),
    original_name varchar(255),
    known_for_department varchar(255),
    popularity float,
    profile_path varchar(255)
);

-- Cast Association
DROP TABLE IF EXISTS staging_series_cast_assoc CASCADE;

CREATE TABLE IF NOT EXISTS staging_series_cast_assoc(
    series_id bigint,
    cast_id bigint,
    character varchar,
    cast_order smallint,
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
    iso_639_1 varchar,
    iso_3166_1 varchar,
    name varchar,
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
    homepage varchar,
    imdb_id varchar(12),
    in_production boolean,
    last_air_date timestamp,
    name varchar,
    number_of_episodes int,
    number_of_seasons int,
    origin_country varchar(64),
    original_language varchar(64),
    original_name varchar,
    overview varchar,
    popularity float,
    poster_path varchar(255),
    status varchar,
    tagline varchar,
    type varchar,
    vote_average float,
    vote_count bigint,
    last_episode_to_air_id bigint,
    next_episode_to_air_id bigint
);

-- Foreign keys are added after all tables exist so the promoted schema matches the
-- ORM-created schema and bulk title deletion removes dependent rows. The two episode
-- references are deferred because the series CSV is loaded before the episode CSVs in
-- the full-sweep transaction.
ALTER TABLE staging_series
    ADD CONSTRAINT fk_series_last_episode_to_air_id
    FOREIGN KEY (last_episode_to_air_id)
    REFERENCES staging_series_last_episode_to_air(id)
    DEFERRABLE INITIALLY DEFERRED,
    ADD CONSTRAINT fk_series_next_episode_to_air_id
    FOREIGN KEY (next_episode_to_air_id)
    REFERENCES staging_series_next_episode_to_air(id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE staging_series_created_by_assoc
    ADD CONSTRAINT fk_series_created_by_assoc_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_series_created_by_assoc_created_by_id
    FOREIGN KEY (created_by_id)
    REFERENCES staging_series_created_by(id) ON DELETE CASCADE;

ALTER TABLE staging_series_genres_assoc
    ADD CONSTRAINT fk_series_genres_assoc_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_series_genres_assoc_genre_id
    FOREIGN KEY (genre_id) REFERENCES staging_series_genres(id) ON DELETE CASCADE;

ALTER TABLE staging_series_networks_assoc
    ADD CONSTRAINT fk_series_networks_assoc_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_series_networks_assoc_network_id
    FOREIGN KEY (network_id)
    REFERENCES staging_series_networks(id) ON DELETE CASCADE;

ALTER TABLE staging_series_companies_assoc
    ADD CONSTRAINT fk_series_companies_assoc_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_series_companies_assoc_company_id
    FOREIGN KEY (company_id)
    REFERENCES staging_series_production_companies(id) ON DELETE CASCADE;

ALTER TABLE staging_series_countries_assoc
    ADD CONSTRAINT fk_series_countries_assoc_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_series_countries_assoc_country_id
    FOREIGN KEY (country_id)
    REFERENCES staging_series_production_countries(iso_3166_1) ON DELETE CASCADE;

ALTER TABLE staging_series_seasons
    ADD CONSTRAINT fk_series_seasons_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE;

ALTER TABLE staging_series_languages_assoc
    ADD CONSTRAINT fk_series_languages_assoc_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_series_languages_assoc_language_id
    FOREIGN KEY (language_id)
    REFERENCES staging_series_spoken_languages(iso_639_1) ON DELETE CASCADE;

ALTER TABLE staging_series_alternative_titles
    ADD CONSTRAINT fk_series_alternative_titles_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE;

ALTER TABLE staging_series_cast_assoc
    ADD CONSTRAINT fk_series_cast_assoc_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_series_cast_assoc_cast_id
    FOREIGN KEY (cast_id)
    REFERENCES staging_series_cast_members(id) ON DELETE CASCADE;

ALTER TABLE staging_series_external_ids
    ADD CONSTRAINT fk_series_external_ids_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE;

ALTER TABLE staging_series_keywords_assoc
    ADD CONSTRAINT fk_series_keywords_assoc_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_series_keywords_assoc_id
    FOREIGN KEY (id) REFERENCES staging_series_keywords(id) ON DELETE CASCADE;

ALTER TABLE staging_series_videos
    ADD CONSTRAINT fk_series_videos_series_id
    FOREIGN KEY (series_id) REFERENCES staging_series(id) ON DELETE CASCADE;
