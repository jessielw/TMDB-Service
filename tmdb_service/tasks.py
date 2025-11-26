import asyncio
import gzip
import json
import shutil
import traceback
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import time

import aiofiles
import aiohttp
from sqlalchemy import delete

from tmdb_service.globals import db, global_config, tmdb_logger
from tmdb_service.models.movies import Movie
from tmdb_service.models.series import Series
from tmdb_service.models.service_metadata import get_metadata, set_metadata
from tmdb_service.tmdb_task_utils import (
    delete_items_from_db,
    extract_id_from_tmdb_url,
    get_tmdb_api_headers,
    insert_movie,
    insert_series,
)


def format_url_with_date(input_str: str) -> str:
    """
    Format TMDB dataset URL with a time delta of 1 day, this prevents
    issues where data sets aren't available due to time issues
    """
    now = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=1)
    return input_str.format(
        month=str(now.month).zfill(2), day=str(now.day).zfill(2), year=str(now.year)
    )


def decompress_gz(gz_path: Path, json_path: Path) -> None:
    """Decompress the gz to the appropriate path"""
    with gzip.open(gz_path, "rb") as s_file, open(json_path, "wb") as d_file:
        shutil.copyfileobj(s_file, d_file, 65536)


async def download_and_extract(url: str, gz_path: Path, json_path: Path) -> Path:
    """Asynchronously download datasets from TMDB"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            if response.status == 200:
                async with aiofiles.open(gz_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(65536):
                        await f.write(chunk)

                # gzip and shutil are sync, so we'll use a thread pool
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, decompress_gz, gz_path, json_path)

                return json_path

            raise Exception("Unable to download TMDB JSON IDs")


async def get_movies_id_url(gz_path: Path, json_path: Path) -> Path:
    """Download TMDB dataset"""
    url = format_url_with_date(
        "http://files.tmdb.org/p/exports/movie_ids_{month}_{day}_{year}.json.gz"
    )
    return await download_and_extract(url, gz_path, json_path)


async def get_series_id_url(gz_path: Path, json_path: Path) -> Path:
    """Download TMDB dataset"""
    url = format_url_with_date(
        "http://files.tmdb.org/p/exports/tv_series_ids_{month}_{day}_{year}.json.gz"
    )
    return await download_and_extract(url, gz_path, json_path)


async def download_tmdb_ids(temp_dir: Path) -> tuple[Path, Path]:
    """Define paths to temp datasets, removes old, downloads new and cleans up after"""
    # paths
    movie_gz = temp_dir / "movie.gz"
    movie_json = temp_dir / "movie_ids.json"
    series_gz = temp_dir / "series.gz"
    series_json = temp_dir / "series_ids.json"

    # movies
    movie_ids = await get_movies_id_url(movie_gz, movie_json)

    # series
    series_ids = await get_series_id_url(series_gz, series_json)

    # clean up gzs
    for item in (movie_gz, series_gz):
        item.unlink()

    return movie_ids, series_ids


def get_movie_urls(ids) -> list[str]:
    """Return list of URLs"""
    return [
        f"https://api.themoviedb.org/3/movie/{tmdb_id}?append_to_response=alternative_titles,credits,"
        f"external_ids,keywords,release_dates,videos"
        for tmdb_id in ids
    ]


def get_series_urls(ids) -> list[str]:
    """Return list of URLs"""
    return [
        f"https://api.themoviedb.org/3/tv/{tmdb_id}?append_to_response=alternative_titles,credits,"
        f"external_ids,keywords,videos"
        for tmdb_id in ids
    ]


async def fetch_tmdb(
    session: aiohttp.ClientSession,
    url: str,
    headers: dict,
) -> dict | None | bool:
    """Fetch TMDB API results"""
    MAX_RETRIES = 10
    RETRY_DELAY = 2

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 404:
                    tmdb_logger.debug(f"404 Not Found for {url}, skipping retries.")
                    return False
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == MAX_RETRIES:
                tmdb_logger.warning(f"Failed to get data from TMDB API ({url} - {e}) ")
                return None
            tmdb_logger.warning(
                f"Retry {attempt}/{MAX_RETRIES} for {url} due to client or timeout error."
            )
            await asyncio.sleep(RETRY_DELAY)


async def fetch_and_process(
    urls,
    rate_limit,
    max_connections,
    log_prefix,
    process_batch_fn,
    item_type: str,
) -> None:
    semaphore = asyncio.Semaphore(max_connections)
    headers = get_tmdb_api_headers()
    connector = aiohttp.TCPConnector(limit=max_connections)

    async def fetch_with_semaphore(url_for_task: str):
        async with semaphore:
            api_result = await fetch_tmdb(session, url_for_task, headers)
            return url_for_task, api_result

    results_batch = []
    ids_to_delete = []
    total_processed_for_ingest = 0
    exceptions = 0
    start_time_loop = time()

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_with_semaphore(url) for url in urls]
        for i, coro_task in enumerate(asyncio.as_completed(tasks), 1):
            # rate limit: space out requests
            now = time()
            expected_time_for_request = i / rate_limit
            elapsed_time = now - start_time_loop
            if elapsed_time < expected_time_for_request:
                await asyncio.sleep(expected_time_for_request - elapsed_time)

            original_url, result_data = await coro_task

            if result_data is False:  # false indicates 404 not found
                item_id = extract_id_from_tmdb_url(original_url)
                if item_id:
                    ids_to_delete.append(item_id)
            elif isinstance(result_data, dict):
                results_batch.append(result_data)
            # result_data is None (other error) or unexpected type
            else:
                exceptions += 1
                if result_data is not None:
                    tmdb_logger.warning(
                        f"Unexpected result type from fetch_tmdb for {original_url}: {type(result_data)}."
                    )

            if len(results_batch) >= global_config.TMDB_BATCH_INSERT:
                tmdb_logger.info(
                    f"{log_prefix}: inserting batch of {len(results_batch)}."
                )
                process_batch_fn(results_batch)
                total_processed_for_ingest += len(results_batch)
                tmdb_logger.info(
                    f"{log_prefix}: inserted {total_processed_for_ingest}/"
                    f"{len(urls) - len(ids_to_delete) - exceptions}."
                )
                results_batch = []

            if i % 1000 == 0:
                tmdb_logger.info(
                    f"{log_prefix}: progress {i}/{len(urls)} requests completed."
                )

        # insert any remaining results
        if results_batch:
            process_batch_fn(results_batch)
            total_processed_for_ingest += len(results_batch)
            tmdb_logger.info(
                f"{log_prefix} Inserted {total_processed_for_ingest}/{len(urls) - len(ids_to_delete) - exceptions}."
            )

        # perform deletions after all fetches are done
        if ids_to_delete:
            tmdb_logger.info(
                f"{log_prefix}: Attempting to delete {len(ids_to_delete)} "
                f"{item_type}(s) if they exist in the database due to 404 responses."
            )
            delete_items_from_db(ids_to_delete, item_type)

    tmdb_logger.debug(
        f"{log_prefix} {exceptions} exceptions out of {len(urls)} requests. "
        f"{len(ids_to_delete)} items marked for deletion."
    )


async def ingest_single_movie(movie_id: int) -> None:
    """Fetch a single movie from TMDB API and add to the database"""
    url = (
        f"https://api.themoviedb.org/3/movie/{movie_id}?append_to_response=alternative_titles,credits,"
        f"external_ids,keywords,release_dates,videos"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=get_tmdb_api_headers()) as response:
            response.raise_for_status()
            data = await response.json()
            insert_movie(data)


async def ingest_single_series(series_id: int):
    """Fetch a single series from TMDB API and add to the database"""
    url = (
        f"https://api.themoviedb.org/3/tv/{series_id}?append_to_response=alternative_titles,credits,"
        f"external_ids,keywords,videos"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=get_tmdb_api_headers()) as response:
            response.raise_for_status()
            data = await response.json()
            insert_series(data)


def add_movies(movies_data: Sequence[dict]) -> None:
    """Add fetched TMDB API data to the database"""
    for movie in movies_data:
        try:
            insert_movie(movie)
        except Exception as e:
            msg = f"{e}\n{traceback.format_exc()}"
            tmdb_logger.error(msg)


def add_series(series_data: Sequence[dict]) -> None:
    """Add fetched TMDB API data to the database"""
    for series in series_data:
        try:
            insert_series(series)
        except Exception as e:
            msg = f"{e}\n{traceback.format_exc()}"
            tmdb_logger.error(msg)


async def update_missing_ids():
    temp_dir = global_config.temp_working_dir / "tmdb_temp_missing"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    # download latest datasets
    movie_ids_path, series_ids_path = await download_tmdb_ids(temp_dir)

    # load all IDs from DB
    with db() as session:
        db_movie_ids = set(r[0] for r in session.query(Movie.id).all())
        db_series_ids = set(r[0] for r in session.query(Series.id).all())

    # find missing movie IDs
    missing_movie_ids = []
    with open(movie_ids_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            if data.get("adult") is True:
                continue
            if data["id"] not in db_movie_ids:
                missing_movie_ids.append(data["id"])

    # find missing series IDs
    missing_series_ids = []
    with open(series_ids_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            if data.get("adult") is True:
                continue
            if data["id"] not in db_series_ids:
                missing_series_ids.append(data["id"])

    tmdb_logger.info(
        f"Missing movies: {len(missing_movie_ids)}, missing series: {len(missing_series_ids)}"
    )

    # ingest only missing IDs
    if missing_movie_ids:
        movie_urls = get_movie_urls(missing_movie_ids)
        await fetch_and_process(
            movie_urls,
            rate_limit=global_config.TMDB_RATE_LIMIT
            * global_config.TMDB_MAX_CONNECTIONS,
            max_connections=global_config.TMDB_MAX_CONNECTIONS,
            log_prefix="Missing movies",
            process_batch_fn=add_movies,
            item_type="movie",
        )

    if missing_series_ids:
        series_urls = get_series_urls(missing_series_ids)
        await fetch_and_process(
            series_urls,
            rate_limit=global_config.TMDB_RATE_LIMIT
            * global_config.TMDB_MAX_CONNECTIONS,
            max_connections=global_config.TMDB_MAX_CONNECTIONS,
            log_prefix="Missing series",
            process_batch_fn=add_series,
            item_type="series",
        )


async def prune_deleted_records():
    """
    Downloads latest TMDB ID lists and deletes local records
    (Movies, Series) that are no longer present in the exports.
    """
    start_time = time()
    tmdb_logger.info("Starting pruning of deleted TMDB records...")
    temp_dir = global_config.temp_working_dir / "tmdb_temp_prune"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    try:
        # 1. Download latest ID lists
        tmdb_logger.info("Downloading latest TMDB ID export files...")
        movie_ids_path, series_ids_path = await download_tmdb_ids(temp_dir)
        if not movie_ids_path or not series_ids_path:
            tmdb_logger.error(
                "Failed to download one or both ID files. Aborting prune."
            )
            return

        # 2. Load all IDs from TMDB export files into sets
        tmdb_logger.info("Loading IDs from TMDB export files...")
        tmdb_movie_ids = set()
        tmdb_series_ids = set()

        try:
            with open(movie_ids_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # No adult filter needed here, we want all valid IDs from the export
                        tmdb_movie_ids.add(data["id"])
                    except (json.JSONDecodeError, KeyError):
                        tmdb_logger.warning(
                            f"Skipping invalid line in movie ID file: {line.strip()}"
                        )
                        continue
            tmdb_logger.info(
                f"Loaded {len(tmdb_movie_ids)} movie IDs from TMDB export."
            )

            with open(series_ids_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        tmdb_series_ids.add(data["id"])
                    except (json.JSONDecodeError, KeyError):
                        tmdb_logger.warning(
                            f"Skipping invalid line in series ID file: {line.strip()}"
                        )
                        continue
            tmdb_logger.info(
                f"Loaded {len(tmdb_series_ids)} series IDs from TMDB export."
            )

        except Exception as e:
            tmdb_logger.error(f"Error reading ID export files: {e}")
            raise  # Re-raise to abort if files can't be read

        # 3. Load all IDs from local database tables into sets
        tmdb_logger.info("Loading IDs from local database...")
        local_movie_ids = set()
        local_series_ids = set()
        try:
            with db() as session:
                local_movie_ids = set(r[0] for r in session.query(Movie.id).all())
                tmdb_logger.info(
                    f"Found {len(local_movie_ids)} movie IDs in local database."
                )
                local_series_ids = set(r[0] for r in session.query(Series.id).all())
                tmdb_logger.info(
                    f"Found {len(local_series_ids)} series IDs in local database."
                )
        except Exception as e:
            tmdb_logger.error(f"Error querying local database IDs: {e}")
            raise  # Re-raise to abort if DB query fails

        # 4. Find IDs to delete (present locally, but not in TMDB exports)
        movie_ids_to_delete = local_movie_ids - tmdb_movie_ids
        series_ids_to_delete = local_series_ids - tmdb_series_ids

        tmdb_logger.info(f"Found {len(movie_ids_to_delete)} movies to prune.")
        tmdb_logger.info(f"Found {len(series_ids_to_delete)} series to prune.")

        # 5. Perform deletions (using bulk delete for efficiency)
        if movie_ids_to_delete:
            tmdb_logger.info("Deleting movies...")
            # Convert set to list for potential chunking if needed, though usually fine
            movie_ids_list = list(movie_ids_to_delete)
            try:
                with db() as session:
                    # Use SQLAlchemy Core delete for bulk operation
                    stmt = delete(Movie).where(Movie.id.in_(movie_ids_list))
                    result = session.execute(stmt)
                    session.commit()
                    tmdb_logger.info(f"Deleted {result.rowcount} movies.")
            except Exception as e:
                tmdb_logger.error(f"Error deleting movies: {e}")
                # Optionally rollback or log specific IDs that failed

        if series_ids_to_delete:
            tmdb_logger.info("Deleting series...")
            series_ids_list = list(series_ids_to_delete)
            try:
                with db() as session:
                    stmt = delete(Series).where(Series.id.in_(series_ids_list))
                    result = session.execute(stmt)
                    session.commit()
                    tmdb_logger.info(f"Deleted {result.rowcount} series.")
            except Exception as e:
                tmdb_logger.error(f"Error deleting series: {e}")

    except Exception as e:
        tmdb_logger.error(f"Error during prune operation: {e}")
        tmdb_logger.error(traceback.format_exc())
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        tmdb_logger.debug(f"Cleaned up temp directory {temp_dir}")

    end_time = time()
    tmdb_logger.info(
        f"Pruning completed: Elapsed time = {end_time - start_time:.2f} seconds"
    )


async def fetch_all_tmdb_changes(
    endpoint: str, start_date: str | None = None, end_date: str | None = None
) -> list[dict]:
    """Fetch all changed IDs from TMDB, handling pagination with 500-page API limit."""
    headers = get_tmdb_api_headers()
    base_url = f"https://api.themoviedb.org/3/{endpoint}"
    params = []
    if start_date:
        params.append(f"start_date={start_date}")
    if end_date:
        params.append(f"end_date={end_date}")
    params_str = "&".join(params)
    url = f"{base_url}?{params_str}" if params_str else base_url

    results = []
    page = 1
    total_pages = 1
    MAX_PAGE = 500  # TMDB API hard limit

    async with aiohttp.ClientSession() as session:
        while page <= total_pages and page <= MAX_PAGE:
            paged_url = f"{url}&page={page}" if "?" in url else f"{url}?page={page}"
            async with session.get(paged_url, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                results.extend(data.get("results", []))
                total_pages = data.get("total_pages", 1)
                page += 1

        if total_pages > MAX_PAGE:
            tmdb_logger.warning(
                f"{endpoint}: Hit TMDB API page limit ({MAX_PAGE}). "
                f"Retrieved {len(results)} changes, but {total_pages} pages exist. "
                f"Consider running changes sync more frequently or using shorter date ranges."
            )

    return results


async def process_tmdb_changes_sync():
    """Sync only changed movies and series from TMDB."""
    # get the last sync time, default to 14 days ago (TMDB API max)
    with db() as session:
        last_sync = get_metadata(session, "last_changes_sync")

    if last_sync:
        start_date = datetime.fromisoformat(last_sync)
        # ensure we don't query more than 14 days (TMDB API limit)
        earliest_allowed = datetime.now(timezone.utc) - timedelta(days=14)
        if start_date < earliest_allowed:
            tmdb_logger.warning(
                f"Last sync was {start_date}, more than 14 days ago. "
                f"Using 14-day look back (TMDB API limit)."
            )
            start_date = earliest_allowed
    else:
        # first run: look back 14 days (max allowed by TMDB)
        start_date = datetime.now(timezone.utc) - timedelta(days=14)
        tmdb_logger.info("No previous sync found, using 14-day look back.")

    end_date = datetime.now(timezone.utc)

    # calculate total days in the range
    total_days = (end_date - start_date).days

    # Split into chunks to avoid hitting the 500-page limit (50,000 items max)
    # With 100 items per page, 500 pages = 50,000 items.
    # To be safe, we'll use smaller chunks: 1-day chunks for ranges > 3 days
    if total_days > 3:
        chunk_days = 1  # Process 1 day at a time to minimize pagination issues
        tmdb_logger.info(
            f"Date range is {total_days} days. "
            f"Processing in 1-day chunks to avoid API pagination limits."
        )
    else:
        chunk_days = max(1, total_days)  # For 1-3 day ranges, process all at once

    all_movie_ids = []
    all_series_ids = []

    # process in chunks
    current_start = start_date
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=chunk_days), end_date)
        start_str = current_start.strftime("%Y-%m-%d")
        end_str = current_end.strftime("%Y-%m-%d")

        tmdb_logger.info(f"Syncing changes from {start_str} to {end_str}")

        # fetch changed movie IDs for this chunk
        movie_changes = await fetch_all_tmdb_changes(
            "movie/changes", start_date=start_str, end_date=end_str
        )
        chunk_movie_ids = [
            item["id"] for item in movie_changes if item.get("adult") is not True
        ]
        all_movie_ids.extend(chunk_movie_ids)

        # fetch changed series IDs for this chunk
        series_changes = await fetch_all_tmdb_changes(
            "tv/changes", start_date=start_str, end_date=end_str
        )
        chunk_series_ids = [
            item["id"] for item in series_changes if item.get("adult") is not True
        ]
        all_series_ids.extend(chunk_series_ids)

        tmdb_logger.info(
            f"Chunk {start_str} to {end_str}: "
            f"{len(chunk_movie_ids)} movies, {len(chunk_series_ids)} series"
        )

        current_start = current_end

    # deduplicate IDs (same item might have changed multiple times)
    movie_ids = list(set(all_movie_ids))
    series_ids = list(set(all_series_ids))

    tmdb_logger.info(
        f"Total unique changes: {len(movie_ids)} movies, {len(series_ids)} series."
    )

    # fetch and update changed movies
    if movie_ids:
        movie_urls = get_movie_urls(movie_ids)
        await fetch_and_process(
            movie_urls,
            rate_limit=global_config.TMDB_RATE_LIMIT
            * global_config.TMDB_MAX_CONNECTIONS,
            max_connections=global_config.TMDB_MAX_CONNECTIONS,
            log_prefix="Changes sync movies",
            process_batch_fn=add_movies,
            item_type="movie",
        )

    # fetch and update changed series
    if series_ids:
        series_urls = get_series_urls(series_ids)
        await fetch_and_process(
            series_urls,
            rate_limit=global_config.TMDB_RATE_LIMIT
            * global_config.TMDB_MAX_CONNECTIONS,
            max_connections=global_config.TMDB_MAX_CONNECTIONS,
            log_prefix="Changes sync series",
            process_batch_fn=add_series,
            item_type="series",
        )

    # update the last sync time after successful completion
    with db() as session:
        set_metadata(
            session, "last_changes_sync", datetime.now(timezone.utc).isoformat()
        )
        session.commit()
    tmdb_logger.info("Changes sync metadata timestamp updated.")
