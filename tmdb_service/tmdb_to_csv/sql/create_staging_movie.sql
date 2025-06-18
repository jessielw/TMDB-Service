-- Movie Collections
DROP TABLE IF EXISTS staging_movie_collections CASCADE;

CREATE TABLE staging_movie_collections(
    id bigint PRIMARY KEY,
    name text,
    poster_path varchar(255),
    backdrop_path varchar(255)
);

-- Movie Genres
DROP TABLE IF EXISTS staging_movie_genres CASCADE;

CREATE TABLE staging_movie_genres(
    id bigint PRIMARY KEY,
    name varchar(255)
);

-- Movie Genres Association
DROP TABLE IF EXISTS staging_movie_genres_assoc CASCADE;

CREATE TABLE staging_movie_genres_assoc(
    movie_id bigint,
    genre_id bigint,
    PRIMARY KEY (movie_id, genre_id)
);

-- Movie Production Companies
DROP TABLE IF EXISTS staging_movie_production_companies CASCADE;

CREATE TABLE staging_movie_production_companies(
    id bigint PRIMARY KEY,
    name text,
    origin_country varchar(255),
    logo_path varchar(255)
);

-- Movie Companies Association
DROP TABLE IF EXISTS staging_movie_companies_assoc CASCADE;

CREATE TABLE staging_movie_companies_assoc(
    movie_id bigint,
    company_id bigint,
    PRIMARY KEY (movie_id, company_id)
);

-- Movie Production Countries
DROP TABLE IF EXISTS staging_movie_production_countries CASCADE;

CREATE TABLE staging_movie_production_countries(
    iso_3166_1 text PRIMARY KEY,
    name text
);

-- Movie Countries Association
DROP TABLE IF EXISTS staging_movie_countries_assoc CASCADE;

CREATE TABLE staging_movie_countries_assoc(
    movie_id bigint,
    country_id text,
    PRIMARY KEY (movie_id, country_id)
);

-- Movie Spoken Languages
DROP TABLE IF EXISTS staging_movie_spoken_languages CASCADE;

CREATE TABLE staging_movie_spoken_languages(
    iso_639_1 text PRIMARY KEY,
    english_name varchar(255),
    name varchar(255)
);

-- Movie Languages Association
DROP TABLE IF EXISTS staging_movie_languages_assoc CASCADE;

CREATE TABLE staging_movie_languages_assoc(
    movie_id bigint,
    language_id text,
    PRIMARY KEY (movie_id, language_id)
);

-- Movie Alternative Titles
DROP TABLE IF EXISTS staging_movie_alternative_titles CASCADE;

CREATE TABLE staging_movie_alternative_titles(
    id bigserial PRIMARY KEY,
    iso_3166_1 text,
    title text,
    type TEXT,
    movie_id bigint
);

-- Movie Cast Members
DROP TABLE IF EXISTS staging_movie_cast_members CASCADE;

CREATE TABLE staging_movie_cast_members(
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

-- Movie Cast Association
DROP TABLE IF EXISTS staging_movie_cast_assoc CASCADE;

CREATE TABLE staging_movie_cast_assoc(
    movie_id bigint,
    cast_id bigint,
    PRIMARY KEY (movie_id, cast_id)
);

-- Movie External IDs
DROP TABLE IF EXISTS staging_movie_external_ids CASCADE;

CREATE TABLE staging_movie_external_ids(
    movie_id bigint PRIMARY KEY,
    imdb_id varchar(255),
    wikidata_id varchar(255),
    facebook_id varchar(255),
    instagram_id varchar(255),
    twitter_id varchar(255)
);

-- Movie Keywords
DROP TABLE IF EXISTS staging_movie_keywords CASCADE;

CREATE TABLE staging_movie_keywords(
    id bigint PRIMARY KEY,
    name varchar(255)
);

-- Movie Keywords Association
DROP TABLE IF EXISTS staging_movie_keywords_assoc CASCADE;

CREATE TABLE staging_movie_keywords_assoc(
    movie_id bigint,
    id bigint,
    PRIMARY KEY (movie_id, id)
);

-- Movie Release Dates
DROP TABLE IF EXISTS staging_movie_release_dates CASCADE;

CREATE TABLE staging_movie_release_dates(
    id bigserial PRIMARY KEY,
    iso_3166_1 text,
    certification text,
    release_date timestamp,
    type INT,
    note text,
    movie_id bigint
);

-- Movie Videos
DROP TABLE IF EXISTS staging_movie_videos CASCADE;

CREATE TABLE staging_movie_videos(
    id varchar(255) PRIMARY KEY,
    iso_639_1 text,
    iso_3166_1 text,
    name text,
    key VARCHAR(255),
    site varchar(255),
    size int,
    type VARCHAR(255),
    official boolean,
    published_at timestamp,
    movie_id bigint
);

-- Movie
DROP TABLE IF EXISTS staging_movie CASCADE;

CREATE TABLE staging_movie(
    id bigint PRIMARY KEY,
    backdrop_path varchar(255),
    budget bigint,
    homepage text,
    imdb_id varchar(12),
    origin_country text,
    original_language varchar(64),
    original_title text,
    overview text,
    popularity float,
    poster_path varchar(255),
    release_date timestamp,
    revenue bigint,
    runtime int,
    status text,
    tagline text,
    title text,
    video boolean,
    vote_average float,
    vote_count bigint,
    belongs_to_collection_id bigint
);

