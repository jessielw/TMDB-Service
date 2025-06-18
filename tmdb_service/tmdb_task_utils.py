from collections.abc import Callable, Sequence
from datetime import datetime
import re
from typing import Any

from sqlalchemy import delete as db_delete

from tmdb_service.globals import db, global_config, tmdb_logger
from tmdb_service.models.movies import (
    Movie,
    MovieAlternativeTitles,
    MovieCastMembers,
    MovieCollections,
    MovieExternalIDs,
    MovieGenres,
    MovieKeywords,
    MovieProductionCompanies,
    MovieProductionCountries,
    MovieReleaseDates,
    MovieSpokenLanguages,
    MovieVideos,
)
from tmdb_service.models.series import (
    Series,
    SeriesAlternativeTitles,
    SeriesCastMembers,
    SeriesCreatedBy,
    SeriesExternalIDs,
    SeriesGenres,
    SeriesKeywords,
    SeriesLastEpisodeToAir,
    SeriesNetworks,
    SeriesNextEpisodeToAir,
    SeriesProductionCompanies,
    SeriesProductionCountries,
    SeriesSeasons,
    SeriesSpokenLanguages,
    SeriesVideos,
)


def get_tmdb_api_headers() -> dict:
    """Return authenticated TMDB API headers"""
    return {
        "accept": "application/json",
        "Authorization": f"Bearer {global_config.TMDB_READ_ACCESS_TOKEN}",
    }


def parse_datetime(dt_str: str | None) -> datetime | None:
    """Parse both date and datetime strings"""
    if not dt_str:
        return None
    try:
        if "T" in dt_str:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        else:
            return datetime.strptime(dt_str, "%Y-%m-%d")
    except Exception:
        return None


def get_or_create(session, model, pk_dict: dict, defaults: Any = None) -> Any:
    obj = session.get(
        model,
        tuple(pk_dict.values()) if len(pk_dict) > 1 else list(pk_dict.values())[0],
    )
    if obj:
        if defaults:
            for k, v in defaults.items():
                setattr(obj, k, v)
        return obj
    params = {**pk_dict}
    if defaults:
        params.update(defaults)
    obj = model(**params)
    session.add(obj)
    return obj


def de_dupe_by_key(items: Sequence[Any], key_func: Callable) -> list:
    seen = {}
    for item in items:
        seen[key_func(item)] = item
    return list(seen.values())


def extract_id_from_tmdb_url(url: str) -> int | None:
    """Extracts the TMDB ID from a movie or TV API URL."""
    match = re.search(r"/(?:movie|tv)/(\d+)", url)
    if match:
        return int(match.group(1))
    tmdb_logger.warning(f"Could not extract ID from URL: {url}.")
    return None


def delete_items_from_db(item_ids: list[int], item_type: str) -> None:
    """Deletes movies or series from the database by their IDs."""
    if not item_ids:
        return

    with db() as session:
        try:
            deleted_count = 0
            if item_type == "movie":
                stmt = db_delete(Movie).where(Movie.id.in_(item_ids))
                result = session.execute(stmt)
                deleted_count = result.rowcount
            elif item_type == "series":
                stmt = db_delete(Series).where(Series.id.in_(item_ids))
                result = session.execute(stmt)
                deleted_count = result.rowcount
            else:
                tmdb_logger.error(
                    f"Unknown item type for deletion: {item_type}. IDs: {item_ids}."
                )
                return

            session.commit()
            tmdb_logger.info(
                f"Successfully deleted {deleted_count} {item_type}(s) from the database (attempted {len(item_ids)})."
            )
        except Exception as e:
            tmdb_logger.error(
                f"Error deleting {item_type}s ({item_ids}): {e}", exc_info=True
            )
            session.rollback()


def insert_movie(movie_data: dict) -> None:
    """Ingest movie data from TMDB API, replacing all relationship data."""
    with db() as session:
        try:
            movie_id = movie_data["id"]

            # get the movie if it exists
            movie = session.get(Movie, movie_id)

            # clear all relationship data if exists
            if movie:
                # many-to-many
                movie.genres.clear()
                movie.production_companies.clear()
                movie.production_countries.clear()
                movie.spoken_languages.clear()
                movie.cast_members.clear()
                movie.keywords.clear()
            else:
                movie = Movie(id=movie_id)
                session.add(movie)

            # add genres
            genres = [
                get_or_create(
                    session, MovieGenres, {"id": g["id"]}, {"name": g["name"]}
                )
                for g in movie_data.get("genres", [])
            ]
            genres = de_dupe_by_key(genres, lambda g: g.id)

            # add companies
            companies = [
                get_or_create(
                    session,
                    MovieProductionCompanies,
                    {"id": pc["id"]},
                    {
                        "name": pc["name"],
                        "origin_country": pc["origin_country"],
                        "logo_path": pc["logo_path"],
                    },
                )
                for pc in movie_data.get("production_companies", [])
            ]
            companies = de_dupe_by_key(companies, lambda c: c.id)

            # add countries
            countries = [
                get_or_create(
                    session,
                    MovieProductionCountries,
                    {"iso_3166_1": pc["iso_3166_1"]},
                    {"name": pc["name"]},
                )
                for pc in movie_data.get("production_countries", [])
            ]
            countries = de_dupe_by_key(countries, lambda c: c.iso_3166_1)

            # add languages
            languages = [
                get_or_create(
                    session,
                    MovieSpokenLanguages,
                    {"iso_639_1": lang["iso_639_1"]},
                    {"english_name": lang["english_name"], "name": lang["name"]},
                )
                for lang in movie_data.get("spoken_languages", [])
            ]
            languages = de_dupe_by_key(languages, lambda lang: lang.iso_639_1)

            # add cast members
            cast_members = [
                get_or_create(
                    session,
                    MovieCastMembers,
                    {"id": cm["id"]},
                    {
                        "gender": cm["gender"],
                        "cast_id": cm["cast_id"],
                        "name": cm["name"],
                        "original_name": cm["original_name"],
                        "known_for_department": cm["known_for_department"],
                        "popularity": cm["popularity"],
                        "profile_path": cm["profile_path"],
                        "character": cm["character"],
                        "cast_order": cm["order"],
                    },
                )
                for cm in movie_data.get("credits", {}).get("cast", [])
            ]
            cast_members = de_dupe_by_key(cast_members, lambda c: c.id)

            # add keywords
            keywords = [
                get_or_create(
                    session, MovieKeywords, {"id": kw["id"]}, {"name": kw["name"]}
                )
                for kw in movie_data.get("keywords", {}).get("keywords", [])
            ]
            keywords = de_dupe_by_key(keywords, lambda k: k.id)

            # add videos
            videos = [
                get_or_create(
                    session,
                    MovieVideos,
                    {"id": vid["id"]},
                    {
                        "iso_639_1": vid.get("iso_639_1"),
                        "iso_3166_1": vid.get("iso_3166_1"),
                        "name": vid.get("name"),
                        "key": vid.get("key"),
                        "site": vid.get("site"),
                        "size": vid.get("size"),
                        "type": vid.get("type"),
                        "official": vid.get("official"),
                        "published_at": parse_datetime(vid.get("published_at")),
                    },
                )
                for vid in movie_data.get("videos", {}).get("results", [])
            ]
            videos = de_dupe_by_key(videos, lambda v: v.id)

            # add collections
            collection = None
            if movie_data.get("belongs_to_collection") and movie_data[
                "belongs_to_collection"
            ].get("id"):
                c = movie_data["belongs_to_collection"]
                collection = get_or_create(
                    session,
                    MovieCollections,
                    {"id": c["id"]},
                    {
                        "name": c.get("name"),
                        "poster_path": c.get("poster_path"),
                        "backdrop_path": c.get("backdrop_path"),
                    },
                )

            # add external ids
            ext_ids = (
                session.query(MovieExternalIDs)
                .filter_by(movie_id=movie_data["id"])
                .first()
            )
            if not ext_ids:
                ext_ids = MovieExternalIDs(movie_id=movie_data["id"])
                session.add(ext_ids)
            ext_data = movie_data["external_ids"]
            ext_ids.imdb_id = ext_data.get("imdb_id")
            ext_ids.wikidata_id = ext_data.get("wikidata_id")
            ext_ids.facebook_id = ext_data.get("facebook_id")
            ext_ids.instagram_id = ext_data.get("instagram_id")
            ext_ids.twitter_id = ext_data.get("twitter_id")

            # add alternative titles
            alt_titles = [
                MovieAlternativeTitles(
                    iso_3166_1=alt_title["iso_3166_1"],
                    title=alt_title["title"],
                    type=alt_title.get("type"),
                    movie_id=movie_data["id"],
                )
                for alt_title in movie_data.get("alternative_titles", {}).get(
                    "titles", []
                )
            ]

            # add release dates
            release_dates = [
                MovieReleaseDates(
                    iso_3166_1=rd_group.get("iso_3166_1"),
                    certification=release.get("certification"),
                    release_date=parse_datetime(release.get("release_date")),
                    type=release.get("type"),
                    note=release.get("note"),
                    movie_id=movie_data["id"],
                )
                for rd_group in movie_data.get("release_dates", {}).get("results", [])
                for release in rd_group.get("release_dates", [])
            ]

            # add remaining scaler fields
            movie.backdrop_path = movie_data.get("backdrop_path")
            movie.budget = movie_data.get("budget")
            movie.homepage = movie_data.get("homepage")
            movie.imdb_id = movie_data.get("imdb_id")
            movie.origin_country = (
                movie_data.get("origin_country", [None])[0]
                if movie_data.get("origin_country")
                else None
            )
            movie.original_language = movie_data.get("original_language")
            movie.original_title = movie_data.get("original_title")
            movie.overview = movie_data.get("overview")
            movie.popularity = movie_data.get("popularity")
            movie.poster_path = movie_data.get("poster_path")
            movie.release_date = parse_datetime(movie_data.get("release_date"))
            movie.revenue = movie_data.get("revenue")
            movie.runtime = movie_data.get("runtime")
            movie.status = movie_data.get("status")
            movie.tagline = movie_data.get("tagline")
            movie.title = movie_data.get("title")
            movie.video = movie_data.get("video")
            movie.vote_average = movie_data.get("vote_average")
            movie.vote_count = movie_data.get("vote_count")

            # assign all relationships
            movie.belongs_to_collection = collection
            movie.genres = genres
            movie.production_companies = companies
            movie.production_countries = countries
            movie.spoken_languages = languages
            movie.cast_members = cast_members
            movie.external_ids = ext_ids
            movie.keywords = keywords
            movie.release_dates = release_dates
            movie.videos = videos
            movie.alternative_titles = alt_titles

            session.commit()
        except Exception:
            session.rollback()
            raise


def insert_series(series_data: dict) -> None:
    """Ingest series data from TMDB API, replacing all relationship data."""
    with db() as session:
        try:
            series_id = series_data["id"]

            # get the series if it exists
            series = session.get(Series, series_id)

            # clear relationship data if series exists
            if series:
                # many-to-many relationships
                series.genres.clear()
                series.production_companies.clear()
                series.production_countries.clear()
                series.spoken_languages.clear()
                series.cast_members.clear()
                series.keywords.clear()
                series.networks.clear()
                series.created_by.clear()
            else:
                series = Series(id=series_id)
                session.add(series)

            # add genres
            genres = [
                get_or_create(
                    session, SeriesGenres, {"id": g["id"]}, {"name": g["name"]}
                )
                for g in series_data.get("genres", [])
            ]
            genres = de_dupe_by_key(genres, lambda g: g.id)

            # add companies
            companies = [
                get_or_create(
                    session,
                    SeriesProductionCompanies,
                    {"id": pc["id"]},
                    {
                        "name": pc["name"],
                        "origin_country": pc["origin_country"],
                        "logo_path": pc["logo_path"],
                    },
                )
                for pc in series_data.get("production_companies", [])
            ]
            companies = de_dupe_by_key(companies, lambda c: c.id)

            # add countries
            countries = [
                get_or_create(
                    session,
                    SeriesProductionCountries,
                    {"iso_3166_1": pc["iso_3166_1"]},
                    {"name": pc["name"]},
                )
                for pc in series_data.get("production_countries", [])
            ]
            countries = de_dupe_by_key(countries, lambda c: c.iso_3166_1)

            # add languages
            languages = [
                get_or_create(
                    session,
                    SeriesSpokenLanguages,
                    {"iso_639_1": lang["iso_639_1"]},
                    {"english_name": lang["english_name"], "name": lang["name"]},
                )
                for lang in series_data.get("spoken_languages", [])
            ]
            languages = de_dupe_by_key(languages, lambda lang: lang.iso_639_1)

            # add cast members
            cast_members = [
                get_or_create(
                    session,
                    SeriesCastMembers,
                    {"id": cm["id"]},
                    {
                        "gender": cm["gender"],
                        "cast_id": cm.get("cast_id"),
                        "name": cm["name"],
                        "original_name": cm["original_name"],
                        "known_for_department": cm["known_for_department"],
                        "popularity": cm["popularity"],
                        "profile_path": cm["profile_path"],
                        "character": cm["character"],
                        "cast_order": cm["order"],
                    },
                )
                for cm in series_data.get("credits", {}).get("cast", [])
            ]
            cast_members = de_dupe_by_key(cast_members, lambda c: c.id)

            # add keywords
            keywords = [
                get_or_create(
                    session, SeriesKeywords, {"id": kw["id"]}, {"name": kw["name"]}
                )
                for kw in series_data.get("keywords", {}).get("results", [])
            ]
            keywords = de_dupe_by_key(keywords, lambda k: k.id)

            # add videos
            videos = [
                get_or_create(
                    session,
                    SeriesVideos,
                    {"id": vid["id"]},
                    {
                        "iso_639_1": vid.get("iso_639_1"),
                        "iso_3166_1": vid.get("iso_3166_1"),
                        "name": vid.get("name"),
                        "key": vid.get("key"),
                        "site": vid.get("site"),
                        "size": vid.get("size"),
                        "type": vid.get("type"),
                        "official": vid.get("official"),
                        "published_at": parse_datetime(vid.get("published_at")),
                    },
                )
                for vid in series_data.get("videos", {}).get("results", [])
            ]
            videos = de_dupe_by_key(videos, lambda v: v.id)

            # add networks
            networks = [
                get_or_create(
                    session,
                    SeriesNetworks,
                    {"id": net["id"]},
                    {
                        "logo_path": net.get("logo_path"),
                        "name": net.get("name"),
                        "origin_country": net.get("origin_country"),
                    },
                )
                for net in series_data.get("networks", [])
            ]
            networks = de_dupe_by_key(networks, lambda n: n.id)

            # add created by
            created_bys = [
                get_or_create(
                    session,
                    SeriesCreatedBy,
                    {"id": cb["id"]},
                    {
                        "credit_id": cb["credit_id"],
                        "name": cb["name"],
                        "original_name": cb["original_name"],
                        "gender": cb["gender"],
                        "profile_path": cb["profile_path"],
                    },
                )
                for cb in series_data.get("created_by", [])
            ]
            created_bys = de_dupe_by_key(created_bys, lambda c: c.id)

            # add last episode to air
            last_ep = None
            if series_data.get("last_episode_to_air"):
                lep = series_data["last_episode_to_air"]
                last_ep = get_or_create(
                    session,
                    SeriesLastEpisodeToAir,
                    {"id": lep.get("id")},
                    {
                        "name": lep.get("name"),
                        "overview": lep.get("overview"),
                        "vote_average": lep.get("vote_average"),
                        "vote_count": lep.get("vote_count"),
                        "air_date": parse_datetime(lep.get("air_date")),
                        "episode_number": lep.get("episode_number"),
                        "episode_type": lep.get("episode_type"),
                        "production_code": lep.get("production_code"),
                        "runtime": lep.get("runtime"),
                        "season_number": lep.get("season_number"),
                        "show_id": lep.get("show_id"),
                        "still_path": lep.get("still_path"),
                    },
                )

            # add next episode to air
            next_ep = None
            if series_data.get("next_episode_to_air"):
                nep = series_data["next_episode_to_air"]
                next_ep = get_or_create(
                    session,
                    SeriesNextEpisodeToAir,
                    {"id": nep.get("id")},
                    {
                        "name": nep.get("name"),
                        "overview": nep.get("overview"),
                        "vote_average": nep.get("vote_average"),
                        "vote_count": nep.get("vote_count"),
                        "air_date": parse_datetime(nep.get("air_date")),
                        "episode_number": nep.get("episode_number"),
                        "episode_type": nep.get("episode_type"),
                        "production_code": nep.get("production_code"),
                        "runtime": nep.get("runtime"),
                        "season_number": nep.get("season_number"),
                        "show_id": nep.get("show_id"),
                        "still_path": nep.get("still_path"),
                    },
                )

            # add seasons
            seasons = [
                get_or_create(
                    session,
                    SeriesSeasons,
                    {"id": season["id"]},
                    {
                        "air_date": parse_datetime(season.get("air_date")),
                        "episode_count": season.get("episode_count"),
                        "name": season.get("name"),
                        "overview": season.get("overview"),
                        "poster_path": season.get("poster_path"),
                        "season_number": season.get("season_number"),
                        "vote_average": season.get("vote_average"),
                    },
                )
                for season in series_data.get("seasons", [])
            ]
            seasons = de_dupe_by_key(seasons, lambda s: s.id)

            # add alternative titles
            alt_titles = [
                SeriesAlternativeTitles(
                    iso_3166_1=alt_title["iso_3166_1"],
                    title=alt_title["title"],
                    type=alt_title.get("type"),
                    series_id=series_data["id"],
                )
                for alt_title in series_data.get("alternative_titles", {}).get(
                    "results", []
                )
            ]

            # add external ids
            ext_ids = (
                session.query(SeriesExternalIDs)
                .filter_by(series_id=series_data["id"])
                .first()
            )
            if not ext_ids:
                ext_ids = SeriesExternalIDs(series_id=series_data["id"])
                session.add(ext_ids)
            ext_data = series_data["external_ids"]
            ext_ids.imdb_id = ext_data.get("imdb_id")
            ext_ids.wikidata_id = ext_data.get("wikidata_id")
            ext_ids.facebook_id = ext_data.get("facebook_id")
            ext_ids.instagram_id = ext_data.get("instagram_id")
            ext_ids.twitter_id = ext_data.get("twitter_id")

            # add scalar fields
            series.backdrop_path = series_data.get("backdrop_path")
            series.first_air_date = parse_datetime(series_data.get("first_air_date"))
            series.homepage = series_data.get("homepage")
            series.imdb_id = series_data.get("imdb_id")
            series.in_production = series_data.get("in_production")
            series.last_air_date = parse_datetime(series_data.get("last_air_date"))
            series.name = series_data.get("name")
            series.number_of_episodes = series_data.get("number_of_episodes")
            series.number_of_seasons = series_data.get("number_of_seasons")
            series.origin_country = (
                series_data.get("origin_country", [None])[0]
                if series_data.get("origin_country")
                else None
            )
            series.original_language = series_data.get("original_language")
            series.original_name = series_data.get("original_name")
            series.overview = series_data.get("overview")
            series.popularity = series_data.get("popularity")
            series.poster_path = series_data.get("poster_path")
            series.status = series_data.get("status")
            series.tagline = series_data.get("tagline")
            series.type = series_data.get("type")
            series.vote_average = series_data.get("vote_average")
            series.vote_count = series_data.get("vote_count")
            series.last_episode_to_air_id = (
                series_data.get("last_episode_to_air", {}).get("id")
                if series_data.get("last_episode_to_air")
                else None
            )
            series.next_episode_to_air_id = (
                series_data.get("next_episode_to_air_id", {}).get("id")
                if series_data.get("next_episode_to_air_id")
                else None
            )

            # assign relationships
            series.created_by = created_bys
            series.genres = genres
            series.last_episode_to_air = last_ep
            series.next_episode_to_air = next_ep
            series.networks = networks
            series.production_companies = companies
            series.production_countries = countries
            series.seasons = seasons
            series.spoken_languages = languages
            series.alternative_titles = alt_titles
            series.cast_members = cast_members
            series.external_ids = ext_ids
            series.keywords = keywords
            series.videos = videos

            session.commit()
        except Exception:
            session.rollback()
            raise
