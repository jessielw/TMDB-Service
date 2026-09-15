"""Pre-Alembic 1.1 schema baseline.

Revision ID: 0001_pre_alembic_1_1
Revises: None
"""

from alembic import op

revision = "0001_pre_alembic_1_1"
down_revision = None
branch_labels = None
depends_on = None


BASELINE_SQL = """
CREATE TABLE movie_collections (
    id BIGINT NOT NULL PRIMARY KEY,
    name VARCHAR,
    poster_path VARCHAR(255),
    backdrop_path VARCHAR(255)
);

CREATE TABLE movie_genres (
    id BIGINT NOT NULL PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE movie_production_companies (
    id BIGINT NOT NULL PRIMARY KEY,
    name VARCHAR,
    origin_country VARCHAR(255),
    logo_path VARCHAR(255)
);

CREATE TABLE movie_production_countries (
    iso_3166_1 VARCHAR NOT NULL PRIMARY KEY,
    name VARCHAR
);

CREATE TABLE movie_spoken_languages (
    iso_639_1 VARCHAR NOT NULL PRIMARY KEY,
    english_name VARCHAR(255),
    name VARCHAR(255)
);

CREATE TABLE movie_cast_members (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    adult BOOLEAN,
    gender SMALLINT,
    cast_id INTEGER,
    name VARCHAR(255),
    original_name VARCHAR(255),
    known_for_department VARCHAR(255),
    popularity FLOAT,
    profile_path VARCHAR(255),
    character VARCHAR,
    cast_order SMALLINT
);

CREATE TABLE movie_keywords (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE series_created_by (
    id BIGINT NOT NULL PRIMARY KEY,
    credit_id VARCHAR(255),
    name VARCHAR,
    original_name VARCHAR,
    gender SMALLINT,
    profile_path VARCHAR(255)
);

CREATE TABLE series_genres (
    id BIGINT NOT NULL PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE series_last_episode_to_air (
    id BIGINT NOT NULL PRIMARY KEY,
    name VARCHAR,
    overview VARCHAR,
    vote_average FLOAT,
    vote_count BIGINT,
    air_date TIMESTAMP WITHOUT TIME ZONE,
    episode_number INTEGER,
    episode_type VARCHAR,
    production_code VARCHAR,
    runtime INTEGER,
    season_number INTEGER,
    show_id INTEGER,
    still_path VARCHAR(255)
);

CREATE TABLE series_next_episode_to_air (
    id BIGINT NOT NULL PRIMARY KEY,
    name VARCHAR,
    overview VARCHAR,
    vote_average FLOAT,
    vote_count BIGINT,
    air_date TIMESTAMP WITHOUT TIME ZONE,
    episode_number INTEGER,
    episode_type VARCHAR,
    production_code VARCHAR,
    runtime INTEGER,
    season_number INTEGER,
    show_id INTEGER,
    still_path VARCHAR(255)
);

CREATE TABLE series_networks (
    id BIGINT NOT NULL PRIMARY KEY,
    logo_path VARCHAR(255),
    name VARCHAR,
    origin_country VARCHAR(64)
);

CREATE TABLE series_production_companies (
    id BIGINT NOT NULL PRIMARY KEY,
    name VARCHAR,
    origin_country VARCHAR(255),
    logo_path VARCHAR(255)
);

CREATE TABLE series_production_countries (
    iso_3166_1 VARCHAR NOT NULL PRIMARY KEY,
    name VARCHAR
);

CREATE TABLE series_spoken_languages (
    iso_639_1 VARCHAR NOT NULL PRIMARY KEY,
    english_name VARCHAR(255),
    name VARCHAR(255)
);

CREATE TABLE series_cast_members (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    adult BOOLEAN,
    gender SMALLINT,
    cast_id INTEGER,
    name VARCHAR(255),
    original_name VARCHAR(255),
    known_for_department VARCHAR(255),
    popularity FLOAT,
    profile_path VARCHAR(255),
    character VARCHAR,
    cast_order SMALLINT
);

CREATE TABLE series_keywords (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE service_metadata (
    key VARCHAR NOT NULL PRIMARY KEY,
    value VARCHAR NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE TABLE movie (
    id BIGINT NOT NULL PRIMARY KEY,
    backdrop_path VARCHAR(255),
    budget BIGINT,
    homepage VARCHAR,
    imdb_id VARCHAR(12),
    origin_country VARCHAR,
    original_language VARCHAR(64),
    original_title VARCHAR,
    overview VARCHAR,
    popularity FLOAT,
    poster_path VARCHAR(255),
    release_date TIMESTAMP WITHOUT TIME ZONE,
    revenue BIGINT,
    runtime INTEGER,
    status VARCHAR,
    tagline VARCHAR,
    title VARCHAR,
    video BOOLEAN,
    vote_average FLOAT,
    vote_count BIGINT,
    belongs_to_collection_id BIGINT REFERENCES movie_collections(id)
);

CREATE TABLE series (
    id BIGINT NOT NULL PRIMARY KEY,
    backdrop_path VARCHAR(255),
    first_air_date TIMESTAMP WITHOUT TIME ZONE,
    homepage VARCHAR,
    imdb_id VARCHAR(12),
    in_production BOOLEAN,
    last_air_date TIMESTAMP WITHOUT TIME ZONE,
    name VARCHAR,
    number_of_episodes INTEGER,
    number_of_seasons INTEGER,
    origin_country VARCHAR(64),
    original_language VARCHAR(64),
    original_name VARCHAR,
    overview VARCHAR,
    popularity FLOAT,
    poster_path VARCHAR(255),
    status VARCHAR,
    tagline VARCHAR,
    type VARCHAR,
    vote_average FLOAT,
    vote_count BIGINT,
    last_episode_to_air_id BIGINT REFERENCES series_last_episode_to_air(id),
    next_episode_to_air_id BIGINT REFERENCES series_next_episode_to_air(id)
);

CREATE TABLE movie_genres_assoc (
    movie_id BIGINT NOT NULL REFERENCES movie(id),
    genre_id BIGINT NOT NULL REFERENCES movie_genres(id),
    PRIMARY KEY (movie_id, genre_id)
);

CREATE TABLE movie_companies_assoc (
    movie_id BIGINT NOT NULL REFERENCES movie(id),
    company_id BIGINT NOT NULL REFERENCES movie_production_companies(id),
    PRIMARY KEY (movie_id, company_id)
);

CREATE TABLE movie_countries_assoc (
    movie_id BIGINT NOT NULL REFERENCES movie(id),
    country_id VARCHAR NOT NULL REFERENCES movie_production_countries(iso_3166_1),
    PRIMARY KEY (movie_id, country_id)
);

CREATE TABLE movie_languages_assoc (
    movie_id BIGINT NOT NULL REFERENCES movie(id),
    language_id VARCHAR NOT NULL REFERENCES movie_spoken_languages(iso_639_1),
    PRIMARY KEY (movie_id, language_id)
);

CREATE TABLE movie_alternative_titles (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    iso_3166_1 VARCHAR,
    title VARCHAR,
    type VARCHAR,
    movie_id BIGINT REFERENCES movie(id)
);

CREATE TABLE movie_cast_assoc (
    movie_id BIGINT NOT NULL REFERENCES movie(id),
    cast_id BIGINT NOT NULL REFERENCES movie_cast_members(id),
    PRIMARY KEY (movie_id, cast_id)
);

CREATE TABLE movie_external_ids (
    movie_id BIGINT NOT NULL PRIMARY KEY REFERENCES movie(id),
    imdb_id VARCHAR(255),
    wikidata_id VARCHAR(255),
    facebook_id VARCHAR(255),
    instagram_id VARCHAR(255),
    twitter_id VARCHAR(255)
);

CREATE TABLE movie_keywords_assoc (
    movie_id BIGINT NOT NULL REFERENCES movie(id),
    id BIGINT NOT NULL REFERENCES movie_keywords(id),
    PRIMARY KEY (movie_id, id)
);

CREATE TABLE movie_release_dates (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    iso_3166_1 VARCHAR,
    certification VARCHAR,
    release_date TIMESTAMP WITHOUT TIME ZONE,
    type INTEGER,
    note VARCHAR,
    movie_id BIGINT REFERENCES movie(id)
);

CREATE TABLE movie_videos (
    id VARCHAR(255) NOT NULL PRIMARY KEY,
    iso_639_1 VARCHAR,
    iso_3166_1 VARCHAR,
    name VARCHAR,
    key VARCHAR(255),
    site VARCHAR(255),
    size INTEGER,
    type VARCHAR(255),
    official BOOLEAN,
    published_at TIMESTAMP WITHOUT TIME ZONE,
    movie_id BIGINT REFERENCES movie(id)
);

CREATE TABLE series_created_by_assoc (
    series_id BIGINT NOT NULL REFERENCES series(id),
    created_by_id BIGINT NOT NULL REFERENCES series_created_by(id),
    PRIMARY KEY (series_id, created_by_id)
);

CREATE TABLE series_genres_assoc (
    series_id BIGINT NOT NULL REFERENCES series(id),
    genre_id BIGINT NOT NULL REFERENCES series_genres(id),
    PRIMARY KEY (series_id, genre_id)
);

CREATE TABLE series_networks_assoc (
    series_id BIGINT NOT NULL REFERENCES series(id),
    network_id BIGINT NOT NULL REFERENCES series_networks(id),
    PRIMARY KEY (series_id, network_id)
);

CREATE TABLE series_companies_assoc (
    series_id BIGINT NOT NULL REFERENCES series(id),
    company_id BIGINT NOT NULL REFERENCES series_production_companies(id),
    PRIMARY KEY (series_id, company_id)
);

CREATE TABLE series_countries_assoc (
    series_id BIGINT NOT NULL REFERENCES series(id),
    country_id VARCHAR NOT NULL REFERENCES series_production_countries(iso_3166_1),
    PRIMARY KEY (series_id, country_id)
);

CREATE TABLE series_seasons (
    id BIGINT NOT NULL PRIMARY KEY,
    air_date TIMESTAMP WITHOUT TIME ZONE,
    episode_count INTEGER,
    name VARCHAR,
    overview VARCHAR,
    poster_path VARCHAR(255),
    season_number INTEGER,
    vote_average FLOAT,
    series_id BIGINT REFERENCES series(id)
);

CREATE TABLE series_languages_assoc (
    series_id BIGINT NOT NULL REFERENCES series(id),
    language_id VARCHAR NOT NULL REFERENCES series_spoken_languages(iso_639_1),
    PRIMARY KEY (series_id, language_id)
);

CREATE TABLE series_alternative_titles (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    iso_3166_1 VARCHAR,
    title VARCHAR,
    type VARCHAR,
    series_id BIGINT REFERENCES series(id)
);

CREATE TABLE series_cast_assoc (
    series_id BIGINT NOT NULL REFERENCES series(id),
    cast_id BIGINT NOT NULL REFERENCES series_cast_members(id),
    PRIMARY KEY (series_id, cast_id)
);

CREATE TABLE series_external_ids (
    series_id BIGINT NOT NULL PRIMARY KEY REFERENCES series(id),
    imdb_id VARCHAR(255),
    wikidata_id VARCHAR(255),
    facebook_id VARCHAR(255),
    instagram_id VARCHAR(255),
    twitter_id VARCHAR(255)
);

CREATE TABLE series_keywords_assoc (
    series_id BIGINT NOT NULL REFERENCES series(id),
    id BIGINT NOT NULL REFERENCES series_keywords(id),
    PRIMARY KEY (series_id, id)
);

CREATE TABLE series_videos (
    id VARCHAR(255) NOT NULL PRIMARY KEY,
    iso_639_1 VARCHAR,
    iso_3166_1 VARCHAR,
    name VARCHAR,
    key VARCHAR(255),
    site VARCHAR(255),
    size INTEGER,
    type VARCHAR(255),
    official BOOLEAN,
    published_at TIMESTAMP WITHOUT TIME ZONE,
    series_id BIGINT REFERENCES series(id)
);

CREATE TABLE job_queue (
    id SERIAL PRIMARY KEY,
    job_type TEXT NOT NULL,
    payload TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE OR REPLACE FUNCTION notify_new_job() RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify('new_job', NEW.id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER job_insert_notify
AFTER INSERT ON job_queue
FOR EACH ROW EXECUTE FUNCTION notify_new_job();
"""


def upgrade() -> None:
    op.execute(BASELINE_SQL)


def downgrade() -> None:
    raise RuntimeError(
        "The TMDB Service Alembic adoption is forward-only; restore a backup to roll back."
    )
