from pathlib import Path
import shutil

from sqlalchemy import Engine, create_engine, text

from tmdb_service.globals import global_config, tmdb_logger
from tmdb_service.tasks import download_tmdb_ids
from tmdb_service.tmdb_task_utils import get_tmdb_api_headers
from tmdb_service.tmdb_to_csv.movies import (
    MOVIE_FIELDNAMES,
    get_movie_copy_commands,
    get_movie_csvs,
    get_movie_dedup_sets,
    process_movies,
)
from tmdb_service.tmdb_to_csv.series import (
    SERIES_FIELDNAMES,
    get_series_copy_commands,
    get_series_csvs,
    get_series_dedup_sets,
    process_series,
)
from tmdb_service.tmdb_to_csv.utils import (
    check_row_count_change,
    close_csv_files,
    open_csv_writers,
    run_sql_script,
    yield_ids,
)


def generate_csvs_dir() -> Path:
    """Generates CSV working directory"""
    csvs_path = Path(global_config.temp_working_dir) / "csvs"
    tmdb_logger.info(f"Generating temp working directory for CSV files: {csvs_path}.")
    if csvs_path.exists():
        shutil.rmtree(csvs_path)
    csvs_path.mkdir()
    tmdb_logger.info("CSV directory created.")
    return csvs_path


def create_staging_tables(engine: Engine, sql_dir: Path) -> None:
    """Create staging tables."""
    tmdb_logger.info("Generating staging tables.")
    run_sql_script(engine, sql_dir / "create_staging_movie.sql")
    run_sql_script(engine, sql_dir / "create_staging_series.sql")
    tmdb_logger.info("Staging tables created.")


def load_staging_tables(engine: Engine, base_path: Path) -> None:
    """Load staging tables, deleting existing staging tables if they exist first."""
    tmdb_logger.info("Loading staging tables with data.")
    sql_copy_commands = get_movie_copy_commands(base_path) + get_series_copy_commands(
        base_path
    )

    with engine.begin() as conn:
        for table, columns, csv_path in sql_copy_commands:
            with open(csv_path, "r") as f:
                sql = f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH CSV HEADER"
                conn.connection.cursor().copy_expert(sql, f)

    tmdb_logger.info("Staging tables loaded.")


def promote_staging_to_production(engine: Engine, sql_dir: Path) -> None:
    """Promote staging tables to production by renaming all tables."""
    tmdb_logger.info("Promoting staging tables to production tables.")
    run_sql_script(
        engine,
        sql_dir / "promote_staging_to_production_movie.sql",
    )
    run_sql_script(
        engine,
        sql_dir / "promote_staging_to_production_series.sql",
    )
    tmdb_logger.info("Staging tables promoted to production.")


def drop_old_tables(engine: Engine, sql_dir: Path) -> None:
    """Drop old tables after rename."""
    tmdb_logger.info("Cleaning up staging tables.")
    run_sql_script(engine, sql_dir / "drop_old_tables_movie.sql")
    run_sql_script(engine, sql_dir / "drop_old_tables_series.sql")
    tmdb_logger.info("Staging tables cleaned up.")


def check_safe_to_promote(first_ingestion: bool, engine: Engine, sql_dir: Path):
    """Check to ensure it's safe to promote staging to production and drop old tables."""
    safe_to_promote = True
    if not first_ingestion:
        for table in ("movie", "series"):  # we'll only check main tables
            staging_table = f"staging_{table}"
            if not check_row_count_change(engine, table, staging_table, threshold=0.5):
                safe_to_promote = False

    if safe_to_promote or first_ingestion:
        # promote staging to production
        promote_staging_to_production(engine, sql_dir)

        # drop old tables
        drop_old_tables(engine, sql_dir)
    else:
        tmdb_logger.error(
            "Aborting promotion and cleanup due to row count check failure."
        )


async def generate_csvs(first_ingestion: bool):
    csvs_path = generate_csvs_dir()
    all_csvs = {**get_movie_csvs(csvs_path), **get_series_csvs(csvs_path)}
    all_fieldnames = {**MOVIE_FIELDNAMES, **SERIES_FIELDNAMES}
    files, writers = open_csv_writers(all_csvs, all_fieldnames)
    dedup_sets = get_movie_dedup_sets() | get_series_dedup_sets()

    tmdb_logger.info("Downloading TMDB ID datasets to generate CSV files.")
    movie_ids_path, series_ids_path = await download_tmdb_ids(
        Path(global_config.temp_working_dir)
    )
    tmdb_logger.info("Datasets downloaded, processing.")

    # get tmdb headers
    headers = get_tmdb_api_headers()

    # count total IDs for progress
    with open(movie_ids_path) as mf:
        total_movie_ids = sum(1 for _ in mf)
    with open(series_ids_path) as tf:
        total_series_ids = sum(1 for _ in tf)

    # counters
    processed_movies = 0
    processed_series = 0

    tmdb_logger.info(
        f"Getting {total_movie_ids} movies data from TMDB and saving to CSV files."
    )
    for movie_id_chunk in yield_ids(movie_ids_path, filter_adult=True, chunk_size=500):
        await process_movies(movie_id_chunk, writers, headers, dedup_sets)
        processed_movies += len(movie_id_chunk)
        tmdb_logger.info(f"Processed {processed_movies}/{total_movie_ids} movies.")

    tmdb_logger.info(
        f"Getting {total_movie_ids} series data from TMDB and saving to CSV files."
    )
    for series_id_chunk in yield_ids(
        series_ids_path, filter_adult=True, chunk_size=500
    ):
        await process_series(series_id_chunk, writers, headers, dedup_sets)
        processed_series += len(series_id_chunk)
        tmdb_logger.info(f"Processed {processed_series}/{total_series_ids} series.")

    tmdb_logger.debug("Closing all CSV files.")
    close_csv_files(files)
    tmdb_logger.debug("CSV files closed.")

    # start sqlalchemy engine
    engine = create_engine(global_config.DATABASE_URI)

    # sql directory
    sql_dir = Path(__file__).parent / "sql"

    # create staging tables
    create_staging_tables(engine, sql_dir)

    # fill staging tables with data
    load_staging_tables(engine, csvs_path)

    # check to ensure it's safe to promote staging to production and drop old tables
    check_safe_to_promote(first_ingestion, engine, sql_dir)

    # apply unaccent
    if global_config.ENABLE_UNACCENT:
        tmdb_logger.info("Adding extension unaccent.")
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))

    # clean up
    tmdb_logger.debug(f"Removing path {csvs_path}.")
    shutil.rmtree(csvs_path)
    tmdb_logger.debug(f"Path {csvs_path} removed.")
