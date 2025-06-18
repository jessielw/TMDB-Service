import asyncio
from pathlib import Path
from typing import Any

import aiohttp

from tmdb_service.globals import global_config, tmdb_logger
from tmdb_service.tasks import fetch_tmdb


def get_series_dedup_sets() -> dict[str, set]:
    return {
        "series_created_by": set(),
        "series_genres": set(),
        "series_genres_assoc": set(),
        "series_last_episode_to_air": set(),
        "series_next_episode_to_air": set(),
        "series_networks": set(),
        "series_networks_assoc": set(),
        "series_production_companies": set(),
        "series_companies_assoc": set(),
        "series_production_countries": set(),
        "series_countries_assoc": set(),
        "series_seasons": set(),
        "series_spoken_languages": set(),
        "series_languages_assoc": set(),
        "series_cast_members": set(),
        "series_cast_assoc": set(),
        "series_external_ids": set(),
        "series_keywords": set(),
        "series_keywords_assoc": set(),
        "series_videos": set(),
    }


def get_series_csvs(base_path: Path) -> dict[str, Path]:
    return {
        "series": base_path / "series.csv",
        "series_created_by": base_path / "series_created_by.csv",
        "series_genres": base_path / "series_genres.csv",
        "series_genres_assoc": base_path / "series_genres_assoc.csv",
        "series_last_episode_to_air": base_path / "series_last_episode_to_air.csv",
        "series_next_episode_to_air": base_path / "series_next_episode_to_air.csv",
        "series_networks": base_path / "series_networks.csv",
        "series_networks_assoc": base_path / "series_networks_assoc.csv",
        "series_production_companies": base_path / "series_production_companies.csv",
        "series_companies_assoc": base_path / "series_companies_assoc.csv",
        "series_production_countries": base_path / "series_production_countries.csv",
        "series_countries_assoc": base_path / "series_countries_assoc.csv",
        "series_seasons": base_path / "series_seasons.csv",
        "series_spoken_languages": base_path / "series_spoken_languages.csv",
        "series_languages_assoc": base_path / "series_languages_assoc.csv",
        "series_alternative_titles": base_path / "series_alternative_titles.csv",
        "series_cast_members": base_path / "series_cast_members.csv",
        "series_cast_assoc": base_path / "series_cast_assoc.csv",
        "series_external_ids": base_path / "series_external_ids.csv",
        "series_keywords": base_path / "series_keywords.csv",
        "series_keywords_assoc": base_path / "series_keywords_assoc.csv",
        "series_videos": base_path / "series_videos.csv",
    }


SERIES_FIELDNAMES = {
    "series": [
        "id",
        "backdrop_path",
        "first_air_date",
        "homepage",
        "imdb_id",
        "in_production",
        "last_air_date",
        "name",
        "number_of_episodes",
        "number_of_seasons",
        "origin_country",
        "original_language",
        "original_name",
        "overview",
        "popularity",
        "poster_path",
        "status",
        "tagline",
        "type",
        "vote_average",
        "vote_count",
        "last_episode_to_air_id",
        "next_episode_to_air_id",
    ],
    "series_created_by": [
        "id",
        "credit_id",
        "name",
        "original_name",
        "gender",
        "profile_path",
    ],
    "series_genres": ["id", "name"],
    "series_genres_assoc": ["series_id", "genre_id"],
    "series_last_episode_to_air": [
        "id",
        "name",
        "overview",
        "vote_average",
        "vote_count",
        "air_date",
        "episode_number",
        "episode_type",
        "production_code",
        "runtime",
        "season_number",
        "show_id",
        "still_path",
    ],
    "series_next_episode_to_air": [
        "id",
        "name",
        "overview",
        "vote_average",
        "vote_count",
        "air_date",
        "episode_number",
        "episode_type",
        "production_code",
        "runtime",
        "season_number",
        "show_id",
        "still_path",
    ],
    "series_networks": ["id", "logo_path", "name", "origin_country"],
    "series_networks_assoc": ["series_id", "network_id"],
    "series_production_companies": ["id", "name", "origin_country", "logo_path"],
    "series_companies_assoc": ["series_id", "company_id"],
    "series_production_countries": ["iso_3166_1", "name"],
    "series_countries_assoc": ["series_id", "country_id"],
    "series_seasons": [
        "id",
        "air_date",
        "episode_count",
        "name",
        "overview",
        "poster_path",
        "season_number",
        "vote_average",
        "series_id",
    ],
    "series_spoken_languages": ["iso_639_1", "english_name", "name"],
    "series_languages_assoc": ["series_id", "language_id"],
    "series_alternative_titles": ["iso_3166_1", "title", "type", "series_id"],
    "series_cast_members": [
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
    "series_cast_assoc": ["series_id", "cast_id"],
    "series_external_ids": [
        "series_id",
        "imdb_id",
        "wikidata_id",
        "facebook_id",
        "instagram_id",
        "twitter_id",
    ],
    "series_keywords": ["id", "name"],
    "series_keywords_assoc": ["series_id", "id"],
    "series_videos": [
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
        "series_id",
    ],
}


async def process_series(
    series_ids: list[int],
    writers: dict[Any, Any],
    headers: dict[Any, Any],
    dedup_sets: dict[str, set[Any]],
) -> None:
    urls = [
        f"https://api.themoviedb.org/3/tv/{series_id}?append_to_response=alternative_titles,credits,"
        f"external_ids,keywords,release_dates,videos"
        for series_id in series_ids
    ]
    connector = aiohttp.TCPConnector(limit=global_config.TMDB_MAX_CONNECTIONS)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_tmdb(session, url, headers) for url in urls]
        for coro in asyncio.as_completed(tasks):
            try:
                data = await coro
                if not data:
                    continue

                writers["series"].writerow(
                    {
                        "id": data.get("id"),
                        "backdrop_path": data.get("backdrop_path"),
                        "first_air_date": data.get("first_air_date"),
                        "homepage": data.get("homepage"),
                        "imdb_id": data.get("external_ids", {}).get("imdb_id")
                        if data.get("external_ids")
                        else None,
                        "in_production": data.get("in_production"),
                        "last_air_date": data.get("last_air_date"),
                        "name": data.get("name"),
                        "number_of_episodes": data.get("number_of_episodes"),
                        "number_of_seasons": data.get("number_of_seasons"),
                        "origin_country": data.get("origin_country"),
                        "original_language": data.get("original_language"),
                        "original_name": data.get("original_name"),
                        "overview": data.get("overview"),
                        "popularity": data.get("popularity"),
                        "poster_path": data.get("poster_path"),
                        "status": data.get("status"),
                        "tagline": data.get("tagline"),
                        "type": data.get("type"),
                        "vote_average": data.get("vote_average"),
                        "vote_count": data.get("vote_count"),
                        "last_episode_to_air_id": (
                            data.get("last_episode_to_air_id") or {}
                        ).get("id"),
                        "next_episode_to_air_id": (
                            data.get("next_episode_to_air") or {}
                        ).get("id"),
                    }
                )

                # --- Created By ---
                for series_created_by in data.get("created_by", {}):
                    series_created_by_id = series_created_by["id"]
                    if series_created_by_id not in dedup_sets["series_created_by"]:
                        writers["series_created_by"].writerow(
                            {
                                "id": series_created_by["id"],
                                "credit_id": series_created_by.get("credit_id"),
                                "name": series_created_by.get("name"),
                                "original_name": series_created_by.get("original_name"),
                                "gender": series_created_by.get("gender"),
                                "profile_path": series_created_by.get("profile_path"),
                            }
                        )
                        dedup_sets["series_created_by"].add(series_created_by_id)

                # --- Genres and Associations ---
                for series_genre in data.get("genres", []):
                    if series_genre["id"] not in dedup_sets["series_genres"]:
                        writers["series_genres"].writerow(
                            {"id": series_genre["id"], "name": series_genre["name"]}
                        )
                        dedup_sets["series_genres"].add(series_genre["id"])
                    assoc_tuple = (data["id"], series_genre["id"])
                    if assoc_tuple not in dedup_sets["series_genres_assoc"]:
                        writers["series_genres_assoc"].writerow(
                            {"series_id": data["id"], "genre_id": series_genre["id"]}
                        )
                        dedup_sets["series_genres_assoc"].add(assoc_tuple)

                # --- Last Episode To Air ---
                last_ep = data.get("last_episode_to_air")
                if last_ep and last_ep.get("id") is not None:
                    last_ep_id = last_ep["id"]
                    if last_ep_id not in dedup_sets["series_last_episode_to_air"]:
                        writers["series_last_episode_to_air"].writerow(
                            {
                                "id": last_ep.get("id"),
                                "name": last_ep.get("name"),
                                "overview": last_ep.get("overview"),
                                "vote_average": last_ep.get("vote_average"),
                                "vote_count": last_ep.get("vote_count"),
                                "air_date": last_ep.get("air_date"),
                                "episode_number": last_ep.get("episode_number"),
                                "episode_type": last_ep.get("episode_type"),
                                "production_code": last_ep.get("production_code"),
                                "runtime": last_ep.get("runtime"),
                                "season_number": last_ep.get("season_number"),
                                "show_id": last_ep.get("show_id"),
                                "still_path": last_ep.get("still_path"),
                            }
                        )
                        dedup_sets["series_last_episode_to_air"].add(last_ep_id)

                # --- Next Episode To Air ---
                next_ep = data.get("next_episode_to_air")
                if next_ep and next_ep.get("id") is not None:
                    next_ep_id = next_ep["id"]
                    if next_ep_id not in dedup_sets["series_next_episode_to_air"]:
                        writers["series_next_episode_to_air"].writerow(
                            {
                                "id": next_ep.get("id"),
                                "name": next_ep.get("name"),
                                "overview": next_ep.get("overview"),
                                "vote_average": next_ep.get("vote_average"),
                                "vote_count": next_ep.get("vote_count"),
                                "air_date": next_ep.get("air_date"),
                                "episode_number": next_ep.get("episode_number"),
                                "episode_type": next_ep.get("episode_type"),
                                "production_code": next_ep.get("production_code"),
                                "runtime": next_ep.get("runtime"),
                                "season_number": next_ep.get("season_number"),
                                "show_id": next_ep.get("show_id"),
                                "still_path": next_ep.get("still_path"),
                            }
                        )
                        dedup_sets["series_next_episode_to_air"].add(next_ep_id)

                # --- Networks and Associations ---
                for network in data.get("networks", []):
                    network_id = network["id"]
                    if network_id not in dedup_sets["series_networks"]:
                        writers["series_networks"].writerow(
                            {
                                "id": network["id"],
                                "logo_path": network.get("logo_path"),
                                "name": network.get("name"),
                                "origin_country": network.get("origin_country"),
                            }
                        )
                        dedup_sets["series_networks"].add(network_id)
                    assoc_tuple = (data["id"], network["id"])
                    if assoc_tuple not in dedup_sets["series_networks_assoc"]:
                        writers["series_networks_assoc"].writerow(
                            {
                                "series_id": data["id"],
                                "network_id": network["id"],
                            }
                        )
                        dedup_sets["series_networks_assoc"].add(assoc_tuple)

                # --- Production Companies and Associations ---
                for company in data.get("production_companies", []):
                    company_id = company.get("id")
                    if company_id not in dedup_sets["series_production_companies"]:
                        writers["series_production_companies"].writerow(
                            {
                                "id": company.get("id"),
                                "name": company.get("name"),
                                "origin_country": company.get("origin_country"),
                                "logo_path": company.get("logo_path"),
                            }
                        )
                        dedup_sets["series_production_companies"].add(company_id)
                    assoc_tuple = (data.get("id"), company.get("id"))
                    if assoc_tuple not in dedup_sets["series_companies_assoc"]:
                        writers["series_companies_assoc"].writerow(
                            {
                                "series_id": data.get("id"),
                                "company_id": company.get("id"),
                            }
                        )
                        dedup_sets["series_companies_assoc"].add(assoc_tuple)

                # --- Production Countries and Associations ---
                for country in data.get("production_countries", []):
                    country_id = country.get("iso_3166_1")
                    if country_id not in dedup_sets["series_production_countries"]:
                        writers["series_production_countries"].writerow(
                            {
                                "iso_3166_1": country.get("iso_3166_1"),
                                "name": country.get("name"),
                            }
                        )
                        dedup_sets["series_production_countries"].add(country_id)
                    assoc_tuple = (data.get("id"), country.get("iso_3166_1"))
                    if assoc_tuple not in dedup_sets["series_countries_assoc"]:
                        writers["series_countries_assoc"].writerow(
                            {
                                "series_id": data.get("id"),
                                "country_id": country.get("iso_3166_1"),
                            }
                        )
                        dedup_sets["series_countries_assoc"].add(assoc_tuple)

                # --- Seasons ---
                for season in data.get("seasons", []):
                    season_id = season["id"]
                    if season_id not in dedup_sets["series_seasons"]:
                        writers["series_seasons"].writerow(
                            {
                                "id": season["id"],
                                "air_date": season.get("air_date"),
                                "episode_count": season.get("episode_count"),
                                "name": season.get("name"),
                                "overview": season.get("overview"),
                                "poster_path": season.get("poster_path"),
                                "season_number": season.get("season_number"),
                                "vote_average": season.get("vote_average"),
                                "series_id": data["id"],
                            }
                        )
                        dedup_sets["series_seasons"].add(season_id)

                # --- Spoken Languages and Associations ---
                for language in data.get("spoken_languages", []):
                    lang_id = language["iso_639_1"]
                    if lang_id not in dedup_sets["series_spoken_languages"]:
                        writers["series_spoken_languages"].writerow(
                            {
                                "iso_639_1": language["iso_639_1"],
                                "english_name": language["english_name"],
                                "name": language["name"],
                            }
                        )
                        dedup_sets["series_spoken_languages"].add(lang_id)
                    assoc_tuple = (data["id"], language["iso_639_1"])
                    if assoc_tuple not in dedup_sets["series_languages_assoc"]:
                        writers["series_languages_assoc"].writerow(
                            {
                                "series_id": data["id"],
                                "language_id": language["iso_639_1"],
                            }
                        )
                        dedup_sets["series_languages_assoc"].add(assoc_tuple)

                # --- Alternative Titles ---
                for alt in data.get("alternative_titles", {}).get("results", []):
                    writers["series_alternative_titles"].writerow(
                        {
                            "iso_3166_1": alt.get("iso_3166_1"),
                            "title": alt.get("title"),
                            "type": alt.get("type"),
                            "series_id": data["id"],
                        }
                    )

                # --- Cast Members and Associations ---
                for cast_member in data.get("credits", {}).get("cast", []):
                    cast_id = cast_member["id"]
                    if cast_id not in dedup_sets["series_cast_members"]:
                        writers["series_cast_members"].writerow(
                            {
                                "id": cast_member["id"],
                                "adult": cast_member["adult"],
                                "gender": cast_member["gender"],
                                "cast_id": cast_id,
                                "name": cast_member["name"],
                                "original_name": cast_member["original_name"],
                                "known_for_department": cast_member[
                                    "known_for_department"
                                ],
                                "popularity": cast_member["popularity"],
                                "profile_path": cast_member["profile_path"],
                                "character": cast_member["character"],
                                "cast_order": cast_member["order"],
                            }
                        )
                        dedup_sets["series_cast_members"].add(cast_id)
                    assoc_tuple = (data["id"], cast_member["id"])
                    if assoc_tuple not in dedup_sets["series_cast_assoc"]:
                        writers["series_cast_assoc"].writerow(
                            {
                                "series_id": data["id"],
                                "cast_id": cast_member["id"],
                            }
                        )
                        dedup_sets["series_cast_assoc"].add(assoc_tuple)

                # --- External IDs ---
                external_ids = data.get("external_ids", {})
                if external_ids:
                    dedup_key = data["id"]
                    if dedup_key not in dedup_sets["series_external_ids"]:
                        writers["series_external_ids"].writerow(
                            {
                                "series_id": data["id"],
                                "imdb_id": external_ids.get("imdb_id"),
                                "wikidata_id": external_ids.get("wikidata_id"),
                                "facebook_id": external_ids.get("facebook_id"),
                                "instagram_id": external_ids.get("instagram_id"),
                                "twitter_id": external_ids.get("twitter_id"),
                            }
                        )
                        dedup_sets["series_external_ids"].add(dedup_key)

                # --- Keywords and Associations ---
                for keyword in data.get("keywords", {}).get("results", []):
                    keyword_id = keyword["id"]
                    if keyword_id not in dedup_sets["series_keywords"]:
                        writers["series_keywords"].writerow(
                            {
                                "id": keyword["id"],
                                "name": keyword["name"],
                            }
                        )
                        dedup_sets["series_keywords"].add(keyword_id)
                    assoc_tuple = (data["id"], keyword["id"])
                    if assoc_tuple not in dedup_sets["series_keywords_assoc"]:
                        writers["series_keywords_assoc"].writerow(
                            {
                                "series_id": data["id"],
                                "id": keyword["id"],
                            }
                        )
                        dedup_sets["series_keywords_assoc"].add(assoc_tuple)

                # --- Videos ---
                for video in data.get("videos", {}).get("results", []):
                    video_id = video["id"]
                    if video_id not in dedup_sets["series_videos"]:
                        writers["series_videos"].writerow(
                            {
                                "id": video["id"],
                                "iso_639_1": video.get("iso_639_1"),
                                "iso_3166_1": video.get("iso_3166_1"),
                                "name": video.get("name"),
                                "key": video.get("key"),
                                "site": video.get("site"),
                                "size": video.get("size"),
                                "type": video.get("type"),
                                "official": video.get("official"),
                                "published_at": video.get("published_at"),
                                "series_id": data["id"],
                            }
                        )
                        dedup_sets["series_videos"].add(video_id)
            except Exception as e:
                tmdb_logger.error(f"Error processing series data: {e}", exc_info=True)


def get_series_copy_commands(base_path: Path) -> list[Any]:
    return [
        (
            "staging_series",
            [
                "id",
                "backdrop_path",
                "first_air_date",
                "homepage",
                "imdb_id",
                "in_production",
                "last_air_date",
                "name",
                "number_of_episodes",
                "number_of_seasons",
                "origin_country",
                "original_language",
                "original_name",
                "overview",
                "popularity",
                "poster_path",
                "status",
                "tagline",
                "type",
                "vote_average",
                "vote_count",
                "last_episode_to_air_id",
                "next_episode_to_air_id",
            ],
            f"{base_path}/series.csv",
        ),
        (
            "staging_series_created_by",
            [
                "id",
                "credit_id",
                "name",
                "original_name",
                "gender",
                "profile_path",
            ],
            f"{base_path}/series_created_by.csv",
        ),
        ("staging_series_genres", ["id", "name"], f"{base_path}/series_genres.csv"),
        (
            "staging_series_genres_assoc",
            ["series_id", "genre_id"],
            f"{base_path}/series_genres_assoc.csv",
        ),
        (
            "staging_series_last_episode_to_air",
            [
                "id",
                "name",
                "overview",
                "vote_average",
                "vote_count",
                "air_date",
                "episode_number",
                "episode_type",
                "production_code",
                "runtime",
                "season_number",
                "show_id",
                "still_path",
            ],
            f"{base_path}/series_last_episode_to_air.csv",
        ),
        (
            "staging_series_next_episode_to_air",
            [
                "id",
                "name",
                "overview",
                "vote_average",
                "vote_count",
                "air_date",
                "episode_number",
                "episode_type",
                "production_code",
                "runtime",
                "season_number",
                "show_id",
                "still_path",
            ],
            f"{base_path}/series_next_episode_to_air.csv",
        ),
        (
            "staging_series_networks",
            ["id", "logo_path", "name", "origin_country"],
            f"{base_path}/series_networks.csv",
        ),
        (
            "staging_series_networks_assoc",
            ["series_id", "network_id"],
            f"{base_path}/series_networks_assoc.csv",
        ),
        (
            "staging_series_production_companies",
            ["id", "name", "origin_country", "logo_path"],
            f"{base_path}/series_production_companies.csv",
        ),
        (
            "staging_series_companies_assoc",
            ["series_id", "company_id"],
            f"{base_path}/series_companies_assoc.csv",
        ),
        (
            "staging_series_production_countries",
            ["iso_3166_1", "name"],
            f"{base_path}/series_production_countries.csv",
        ),
        (
            "staging_series_countries_assoc",
            ["series_id", "country_id"],
            f"{base_path}/series_countries_assoc.csv",
        ),
        (
            "staging_series_seasons",
            [
                "id",
                "air_date",
                "episode_count",
                "name",
                "overview",
                "poster_path",
                "season_number",
                "vote_average",
                "series_id",
            ],
            f"{base_path}/series_seasons.csv",
        ),
        (
            "staging_series_spoken_languages",
            ["iso_639_1", "english_name", "name"],
            f"{base_path}/series_spoken_languages.csv",
        ),
        (
            "staging_series_languages_assoc",
            ["series_id", "language_id"],
            f"{base_path}/series_languages_assoc.csv",
        ),
        (
            "staging_series_alternative_titles",
            ["iso_3166_1", "title", "type", "series_id"],
            f"{base_path}/series_alternative_titles.csv",
        ),
        (
            "staging_series_cast_members",
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
            f"{base_path}/series_cast_members.csv",
        ),
        (
            "staging_series_cast_assoc",
            ["series_id", "cast_id"],
            f"{base_path}/series_cast_assoc.csv",
        ),
        (
            "staging_series_external_ids",
            [
                "series_id",
                "imdb_id",
                "wikidata_id",
                "facebook_id",
                "instagram_id",
                "twitter_id",
            ],
            f"{base_path}/series_external_ids.csv",
        ),
        ("staging_series_keywords", ["id", "name"], f"{base_path}/series_keywords.csv"),
        (
            "staging_series_keywords_assoc",
            ["series_id", "id"],
            f"{base_path}/series_keywords_assoc.csv",
        ),
        (
            "staging_series_videos",
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
                "series_id",
            ],
            f"{base_path}/series_videos.csv",
        ),
    ]
