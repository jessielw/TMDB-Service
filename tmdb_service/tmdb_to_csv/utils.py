from collections.abc import Generator
import csv
import json
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, text

from tmdb_service.globals import tmdb_logger


def open_csv_writers(
    csv_paths: dict[str, Path], fieldnames: dict[str, list[str]]
) -> tuple[dict[Any, Any], dict[Any, Any]]:
    files = {}
    writers = {}
    for key, path in csv_paths.items():
        f = open(path, "w", newline="", encoding="utf-8")
        files[key] = f
        writer = csv.DictWriter(f, fieldnames=fieldnames[key])
        writer.writeheader()
        writers[key] = writer
    return files, writers


def close_csv_files(files: dict[str, Any]) -> None:
    for f in files.values():
        f.close()


def safe_get(d, *keys, default: Any = None) -> Any | None:
    for k in keys:
        if d is None:
            return default
        d = d.get(k)
    return d if d is not None else default


def run_sql_script(engine: Engine, sql_file_path: Path) -> None:
    with engine.begin() as conn:
        with open(sql_file_path, "r") as f:
            sql_commands = f.read()
            conn.execute(text(sql_commands))


def check_row_count_change(
    engine: Engine, prod_table: str, staging_table: str, threshold: float = 0.5
) -> bool:
    with engine.connect() as conn:
        prod_count = None
        staging_count = None
        try:
            prod_count = conn.execute(
                text(f"SELECT COUNT(*) FROM {prod_table}")
            ).scalar()
        except Exception as e:
            tmdb_logger.debug(f"Table {prod_table} likely doesn't exist ({e}).")
        try:
            staging_count = conn.execute(
                text(f"SELECT COUNT(*) FROM {staging_table}")
            ).scalar()
        except Exception as e:
            tmdb_logger.debug(f"Table {staging_table} likely doesn't exist ({e}).")
        if prod_count is not None and staging_count is not None and prod_count > 0:
            # only fail if staging is significantly less than prod
            if staging_count < prod_count:
                change = (prod_count - staging_count) / prod_count
                if change > threshold:
                    tmdb_logger.error(
                        f"Row count for {prod_table} would decrease by {change:.2%} "
                        f"(prod: {prod_count}, staging: {staging_count})"
                    )
                    return False
            tmdb_logger.info(
                f"Row count for {prod_table} OK (prod: {prod_count}, staging: {staging_count})"
            )
        else:
            tmdb_logger.info(
                f"Skipping row count check for {prod_table} (prod: {prod_count}, staging: {staging_count})"
            )
        return True


def yield_ids(
    file_in: Path, filter_adult: bool = True, chunk_size: int = 500
) -> Generator[list[int]]:
    """Yield lists of IDs in chunks"""
    ids = []
    with open(file_in, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            if filter_adult and data.get("adult") is True:
                continue
            ids.append(data["id"])
            if len(ids) >= chunk_size:
                yield ids
                ids = []
        if ids:
            yield ids
