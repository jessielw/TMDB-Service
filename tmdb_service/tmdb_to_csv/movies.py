import asyncio
from pathlib import Path
from typing import Any

import aiohttp

from tmdb_service.globals import global_config, tmdb_logger
from tmdb_service.tasks import fetch_tmdb
from tmdb_service.tmdb_to_csv.utils import safe_get


def get_movie_dedup_sets() -> dict[str, set]:
    return {
        "movie_genres": set(),
        "movie_genres_assoc": set(),
        "movie_collections": set(),
        "movie_production_companies": set(),
        "movie_companies_assoc": set(),
        "movie_production_countries": set(),
        "movie_countries_assoc": set(),
        "movie_spoken_languages": set(),
        "movie_languages_assoc": set(),
        "movie_cast_members": set(),
        "movie_cast_assoc": set(),
        "movie_keywords": set(),
        "movie_keywords_assoc": set(),
        "movie_release_dates": set(),
        "movie_videos": set(),
        "movie_external_ids": set(),
    }


def get_movie_csvs(base_path: Path) -> dict[str, Path]:
    return {
        "movie": base_path / "movie.csv",
        "movie_collections": base_path / "movie_collections.csv",
        "movie_genres": base_path / "movie_genres.csv",
        "movie_genres_assoc": base_path / "movie_genres_assoc.csv",
        "movie_production_companies": base_path / "movie_production_companies.csv",
        "movie_companies_assoc": base_path / "movie_companies_assoc.csv",
        "movie_production_countries": base_path / "movie_production_countries.csv",
        "movie_countries_assoc": base_path / "movie_countries_assoc.csv",
        "movie_spoken_languages": base_path / "movie_spoken_languages.csv",
        "movie_languages_assoc": base_path / "movie_languages_assoc.csv",
        "movie_alternative_titles": base_path / "movie_alternative_titles.csv",
        "movie_cast_members": base_path / "movie_cast_members.csv",
        "movie_cast_assoc": base_path / "movie_cast_assoc.csv",
        "movie_keywords": base_path / "movie_keywords.csv",
        "movie_keywords_assoc": base_path / "movie_keywords_assoc.csv",
        "movie_release_dates": base_path / "movie_release_dates.csv",
        "movie_videos": base_path / "movie_videos.csv",
        "movie_external_ids": base_path / "movie_external_ids.csv",
    }


MOVIE_FIELDNAMES = {
    "movie": [
        "id",
        "backdrop_path",
        "budget",
        "homepage",
        "imdb_id",
        "origin_country",
        "original_language",
        "original_title",
        "overview",
        "popularity",
        "poster_path",
        "release_date",
        "revenue",
        "runtime",
        "status",
        "tagline",
        "title",
        "video",
        "vote_average",
        "vote_count",
        "belongs_to_collection_id",
    ],
    "movie_collections": [
        "id",
        "name",
        "poster_path",
        "backdrop_path",
    ],
    "movie_genres": ["id", "name"],
    "movie_genres_assoc": ["movie_id", "genre_id"],
    "movie_production_companies": ["id", "name", "origin_country", "logo_path"],
    "movie_companies_assoc": ["movie_id", "company_id"],
    "movie_production_countries": ["iso_3166_1", "name"],
    "movie_countries_assoc": ["movie_id", "country_id"],
    "movie_spoken_languages": ["iso_639_1", "english_name", "name"],
    "movie_languages_assoc": ["movie_id", "language_id"],
    "movie_alternative_titles": ["iso_3166_1", "title", "type", "movie_id"],
    "movie_cast_members": [
        "id",
        "adult",
        "gender",
        "cast_id",
        "name",
        "original_name",
        "known_for_department",
        "popularity",
        "profile_path",
        "character",
        "cast_order",
    ],
    "movie_cast_assoc": ["movie_id", "cast_id"],
    "movie_keywords": ["id", "name"],
    "movie_keywords_assoc": ["movie_id", "id"],
    "movie_release_dates": [
        "iso_3166_1",
        "certification",
        "release_date",
        "type",
        "note",
        "movie_id",
    ],
    "movie_videos": [
        "id",
        "iso_639_1",
        "iso_3166_1",
        "name",
        "key",
        "site",
        "size",
        "type",
        "official",
        "published_at",
        "movie_id",
    ],
    "movie_external_ids": [
        "id",
        "imdb_id",
        "wikidata_id",
        "facebook_id",
        "instagram_id",
        "twitter_id",
    ],
}


async def process_movies(
    movie_ids: list[int],
    writers: dict[Any, Any],
    headers: dict[Any, Any],
    dedup_sets: dict[str, set[Any]],
) -> None:
    urls = [
        f"https://api.themoviedb.org/3/movie/{tmdb_id}?append_to_response=alternative_titles,credits,"
        f"external_ids,keywords,release_dates,videos"
        for tmdb_id in movie_ids
    ]
    connector = aiohttp.TCPConnector(limit=global_config.TMDB_MAX_CONNECTIONS)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_tmdb(session, url, headers) for url in urls]
        for coro in asyncio.as_completed(tasks):
            try:
                data = await coro
                if not data:
                    continue

                # --- Main Movie Row ---
                writers["movie"].writerow(
                    {
                        "id": data.get("id"),
                        "backdrop_path": data.get("backdrop_path"),
                        "budget": data.get("budget"),
                        "homepage": data.get("homepage"),
                        "imdb_id": data.get("imdb_id"),
                        "origin_country": data.get("origin_country"),
                        "original_language": data.get("original_language"),
                        "original_title": data.get("original_title"),
                        "overview": data.get("overview"),
                        "popularity": data.get("popularity"),
                        "poster_path": data.get("poster_path"),
                        "release_date": data.get("release_date"),
                        "revenue": data.get("revenue"),
                        "runtime": data.get("runtime"),
                        "status": data.get("status"),
                        "tagline": data.get("tagline"),
                        "title": data.get("title"),
                        "video": data.get("video"),
                        "vote_average": data.get("vote_average"),
                        "vote_count": data.get("vote_count"),
                        "belongs_to_collection_id": safe_get(
                            data, "belongs_to_collection", "id"
                        ),
                    }
                )

                # --- Movie Collection ---
                if "belongs_to_collection" in data and data["belongs_to_collection"]:
                    coll = data["belongs_to_collection"]
                    if coll.get("id") not in dedup_sets["movie_collections"]:
                        writers["movie_collections"].writerow(
                            {
                                "id": coll.get("id"),
                                "name": coll.get("name"),
                                "poster_path": coll.get("poster_path"),
                                "backdrop_path": coll.get("backdrop_path"),
                            }
                        )
                        dedup_sets["movie_collections"].add(coll.get("id"))

                # --- Genres and Associations ---
                for genre in data.get("genres", []):
                    if genre.get("id") not in dedup_sets["movie_genres"]:
                        writers["movie_genres"].writerow(
                            {"id": genre.get("id"), "name": genre.get("name")}
                        )
                        dedup_sets["movie_genres"].add(genre.get("id"))
                    assoc_tuple = (data.get("id"), genre.get("id"))
                    if assoc_tuple not in dedup_sets["movie_genres_assoc"]:
                        writers["movie_genres_assoc"].writerow(
                            {"movie_id": data.get("id"), "genre_id": genre.get("id")}
                        )
                        dedup_sets["movie_genres_assoc"].add(assoc_tuple)

                # --- Production Companies and Associations ---
                for company in data.get("production_companies", []):
                    company_id = company.get("id")
                    if company_id not in dedup_sets["movie_production_companies"]:
                        writers["movie_production_companies"].writerow(
                            {
                                "id": company.get("id"),
                                "name": company.get("name"),
                                "origin_country": company.get("origin_country"),
                                "logo_path": company.get("logo_path"),
                            }
                        )
                        dedup_sets["movie_production_companies"].add(company_id)
                    assoc_tuple = (data.get("id"), company.get("id"))
                    if assoc_tuple not in dedup_sets["movie_companies_assoc"]:
                        writers["movie_companies_assoc"].writerow(
                            {
                                "movie_id": data.get("id"),
                                "company_id": company.get("id"),
                            }
                        )
                        dedup_sets["movie_companies_assoc"].add(assoc_tuple)

                # --- Production Countries and Associations ---
                for country in data.get("production_countries", []):
                    country_id = country.get("iso_3166_1")
                    if country_id not in dedup_sets["movie_production_countries"]:
                        writers["movie_production_countries"].writerow(
                            {
                                "iso_3166_1": country.get("iso_3166_1"),
                                "name": country.get("name"),
                            }
                        )
                        dedup_sets["movie_production_countries"].add(country_id)
                    assoc_tuple = (data.get("id"), country.get("iso_3166_1"))
                    if assoc_tuple not in dedup_sets["movie_countries_assoc"]:
                        writers["movie_countries_assoc"].writerow(
                            {
                                "movie_id": data.get("id"),
                                "country_id": country.get("iso_3166_1"),
                            }
                        )
                        dedup_sets["movie_countries_assoc"].add(assoc_tuple)

                # --- Spoken languages and Associations ---
                for language in data.get("spoken_languages", []):
                    lang_id = language.get("iso_639_1")
                    if lang_id not in dedup_sets["movie_spoken_languages"]:
                        writers["movie_spoken_languages"].writerow(
                            {
                                "iso_639_1": language.get("iso_639_1"),
                                "english_name": language.get("english_name"),
                                "name": language.get("name"),
                            }
                        )
                        dedup_sets["movie_spoken_languages"].add(lang_id)
                    assoc_tuple = (data.get("id"), language.get("iso_639_1"))
                    if assoc_tuple not in dedup_sets["movie_languages_assoc"]:
                        writers["movie_languages_assoc"].writerow(
                            {
                                "movie_id": data.get("id"),
                                "language_id": language.get("iso_639_1"),
                            }
                        )
                        dedup_sets["movie_languages_assoc"].add(assoc_tuple)

                # --- Alternative Titles ---
                for alt in data.get("alternative_titles", {}).get("titles", []):
                    writers["movie_alternative_titles"].writerow(
                        {
                            "iso_3166_1": alt.get("iso_3166_1"),
                            "title": alt.get("title"),
                            "type": alt.get("type"),
                            "movie_id": data.get("id"),
                        }
                    )

                # --- Cast Members and Associations ---
                for cast_member in data.get("credits", {}).get("cast", []):
                    cast_id = cast_member.get("id")
                    if cast_id not in dedup_sets["movie_cast_members"]:
                        writers["movie_cast_members"].writerow(
                            {
                                "id": cast_member.get("id"),
                                "adult": cast_member.get("adult"),
                                "gender": cast_member.get("gender"),
                                "cast_id": cast_member.get("cast_id"),
                                "name": cast_member.get("name"),
                                "original_name": cast_member.get("original_name"),
                                "known_for_department": cast_member.get(
                                    "known_for_department"
                                ),
                                "popularity": cast_member.get("popularity"),
                                "profile_path": cast_member.get("profile_path"),
                                "character": cast_member.get("character"),
                                "cast_order": cast_member.get("order"),
                            }
                        )
                        dedup_sets["movie_cast_members"].add(cast_id)
                    assoc_tuple = (data.get("id"), cast_member.get("id"))
                    if assoc_tuple not in dedup_sets["movie_cast_assoc"]:
                        writers["movie_cast_assoc"].writerow(
                            {
                                "movie_id": data.get("id"),
                                "cast_id": cast_member.get("id"),
                            }
                        )
                        dedup_sets["movie_cast_assoc"].add(assoc_tuple)

                # --- Keywords and Associations ---
                for keyword in data.get("keywords", {}).get("keywords", []):
                    keyword_id = keyword.get("id")
                    if keyword_id not in dedup_sets["movie_keywords"]:
                        writers["movie_keywords"].writerow(
                            {
                                "id": keyword.get("id"),
                                "name": keyword.get("name"),
                            }
                        )
                        dedup_sets["movie_keywords"].add(keyword_id)
                    assoc_tuple = (data.get("id"), keyword.get("id"))
                    if assoc_tuple not in dedup_sets["movie_keywords_assoc"]:
                        writers["movie_keywords_assoc"].writerow(
                            {
                                "movie_id": data.get("id"),
                                "id": keyword.get("id"),
                            }
                        )
                        dedup_sets["movie_keywords_assoc"].add(assoc_tuple)

                # --- Release Dates ---
                for rel in data.get("release_dates", {}).get("results", []):
                    for entry in rel.get("release_dates", []):
                        dedup_tuple = (
                            data.get("id"),
                            rel.get("iso_3166_1"),
                            entry.get("release_date"),
                        )
                        if dedup_tuple not in dedup_sets["movie_release_dates"]:
                            writers["movie_release_dates"].writerow(
                                {
                                    "iso_3166_1": rel.get("iso_3166_1"),
                                    "certification": entry.get("certification"),
                                    "release_date": entry.get("release_date"),
                                    "type": entry.get("type"),
                                    "note": entry.get("note"),
                                    "movie_id": data.get("id"),
                                }
                            )
                            dedup_sets["movie_release_dates"].add(dedup_tuple)

                # --- Videos ---
                for video in data.get("videos", {}).get("results", []):
                    video_id = video.get("id")
                    if video_id not in dedup_sets["movie_videos"]:
                        writers["movie_videos"].writerow(
                            {
                                "id": video.get("id"),
                                "iso_639_1": video.get("iso_639_1"),
                                "iso_3166_1": video.get("iso_3166_1"),
                                "name": video.get("name"),
                                "key": video.get("key"),
                                "site": video.get("site"),
                                "size": video.get("size"),
                                "type": video.get("type"),
                                "official": video.get("official"),
                                "published_at": video.get("published_at"),
                                "movie_id": data.get("id"),
                            }
                        )
                        dedup_sets["movie_videos"].add(video_id)

                # --- External IDs ---
                external_ids = data.get("external_ids", {})
                if external_ids:
                    dedup_key = data.get("id")
                    if dedup_key not in dedup_sets["movie_external_ids"]:
                        writers["movie_external_ids"].writerow(
                            {
                                "id": data.get("id"),
                                "imdb_id": external_ids.get("imdb_id"),
                                "wikidata_id": external_ids.get("wikidata_id"),
                                "facebook_id": external_ids.get("facebook_id"),
                                "instagram_id": external_ids.get("instagram_id"),
                                "twitter_id": external_ids.get("twitter_id"),
                            }
                        )
                        dedup_sets["movie_external_ids"].add(dedup_key)
            except Exception as e:
                tmdb_logger.error(f"Error processing movie data: {e}", exc_info=True)


def get_movie_copy_commands(base_path: Path) -> list[Any]:
    return [
        (
            "staging_movie_collections",
            ["id", "name", "poster_path", "backdrop_path"],
            f"{base_path}/movie_collections.csv",
        ),
        (
            "staging_movie",
            [
                "id",
                "backdrop_path",
                "budget",
                "homepage",
                "imdb_id",
                "origin_country",
                "original_language",
                "original_title",
                "overview",
                "popularity",
                "poster_path",
                "release_date",
                "revenue",
                "runtime",
                "status",
                "tagline",
                "title",
                "video",
                "vote_average",
                "vote_count",
                "belongs_to_collection_id",
            ],
            f"{base_path}/movie.csv",
        ),
        ("staging_movie_genres", ["id", "name"], f"{base_path}/movie_genres.csv"),
        (
            "staging_movie_genres_assoc",
            ["movie_id", "genre_id"],
            f"{base_path}/movie_genres_assoc.csv",
        ),
        (
            "staging_movie_production_companies",
            ["id", "name", "origin_country", "logo_path"],
            f"{base_path}/movie_production_companies.csv",
        ),
        (
            "staging_movie_companies_assoc",
            ["movie_id", "company_id"],
            f"{base_path}/movie_companies_assoc.csv",
        ),
        (
            "staging_movie_production_countries",
            ["iso_3166_1", "name"],
            f"{base_path}/movie_production_countries.csv",
        ),
        (
            "staging_movie_countries_assoc",
            ["movie_id", "country_id"],
            f"{base_path}/movie_countries_assoc.csv",
        ),
        (
            "staging_movie_spoken_languages",
            ["iso_639_1", "english_name", "name"],
            f"{base_path}/movie_spoken_languages.csv",
        ),
        (
            "staging_movie_languages_assoc",
            ["movie_id", "language_id"],
            f"{base_path}/movie_languages_assoc.csv",
        ),
        (
            "staging_movie_alternative_titles",
            ["iso_3166_1", "title", "type", "movie_id"],
            f"{base_path}/movie_alternative_titles.csv",
        ),
        (
            "staging_movie_cast_members",
            [
                "id",
                "adult",
                "gender",
                "cast_id",
                "name",
                "original_name",
                "known_for_department",
                "popularity",
                "profile_path",
                "character",
                "cast_order",
            ],
            f"{base_path}/movie_cast_members.csv",
        ),
        (
            "staging_movie_cast_assoc",
            ["movie_id", "cast_id"],
            f"{base_path}/movie_cast_assoc.csv",
        ),
        (
            "staging_movie_keywords",
            ["id", "name"],
            f"{base_path}/movie_keywords.csv",
        ),
        (
            "staging_movie_keywords_assoc",
            ["movie_id", "id"],
            f"{base_path}/movie_keywords_assoc.csv",
        ),
        (
            "staging_movie_release_dates",
            ["iso_3166_1", "certification", "release_date", "type", "note", "movie_id"],
            f"{base_path}/movie_release_dates.csv",
        ),
        (
            "staging_movie_videos",
            [
                "id",
                "iso_639_1",
                "iso_3166_1",
                "name",
                "key",
                "site",
                "size",
                "type",
                "official",
                "published_at",
                "movie_id",
            ],
            f"{base_path}/movie_videos.csv",
        ),
        (
            "staging_movie_external_ids",
            [
                "movie_id",
                "imdb_id",
                "wikidata_id",
                "facebook_id",
                "instagram_id",
                "twitter_id",
            ],
            f"{base_path}/movie_external_ids.csv",
        ),
    ]
