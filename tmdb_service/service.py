import asyncio
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from functools import partial
import queue
import threading
import traceback
from typing import Any

import aiocron
from cronsim import CronSim
from sqlalchemy import text

from tmdb_service.create_tables import create_tables
from tmdb_service.globals import db, db_engine, global_config, tmdb_logger
from tmdb_service.models.service_metadata import get_metadata, set_metadata
from tmdb_service.notifications import update_media_release_webhook_async
from tmdb_service.tasks import (
    ingest_single_movie,
    ingest_single_series,
    process_tmdb_changes_sync,
    prune_deleted_records,
    update_missing_ids,
)
from tmdb_service.tmdb_to_csv.process import generate_csvs


class TMDBService:
    def __init__(self) -> None:
        self.job_running = False  # for global tasks
        self.active_movie_jobs = 0
        self.lock = asyncio.Lock()
        self.executor = ThreadPoolExecutor(max_workers=1)  # for global tasks
        self.thread_lock = threading.Lock()
        self.movie_lock = threading.Lock()

        # for movie/series added jobs and smaller tasks
        self.task_queue = queue.Queue(maxsize=75)
        self.num_workers = 2

        # start worker threads
        for _ in range(self.num_workers):
            threading.Thread(target=self._task_worker, daemon=True).start()

    def run_global_task_in_thread(
        self, coro_func: Callable[..., Awaitable[Any]], *args, **kwargs
    ) -> bool:
        with self.thread_lock, self.movie_lock:
            if self.job_running or self.active_movie_jobs > 0:
                tmdb_logger.warning(
                    "A global or movie/series job is already running, skipping new global job."
                )
                return False
            self.job_running = True

            def runner():
                try:
                    asyncio.run(
                        self._thread_wrapper(coro_func, *args, **kwargs, is_global=True)
                    )
                except Exception as e:
                    tmdb_logger.error(f"Exception in global thread runner: {e}")

            self.executor.submit(runner)
            return True

    def _task_worker(self):
        while True:
            coro_func, args, kwargs = self.task_queue.get()
            if coro_func is None:
                break
            try:
                asyncio.run(
                    self._thread_wrapper(coro_func, *args, is_global=False, **kwargs)
                )
            except Exception as e:
                tmdb_logger.error(f"Exception in task worker: {e}")
            finally:
                self.task_queue.task_done()

    def run_single_task_in_thread(
        self, coro_func: Callable[..., Awaitable[Any]], *args, **kwargs
    ) -> bool:
        with self.thread_lock, self.movie_lock:
            if self.job_running:
                tmdb_logger.warning(
                    "A global job is running, skipping new movie/series job."
                )
                return False
            self.active_movie_jobs += 1

            try:
                self.task_queue.put_nowait((coro_func, args, kwargs))
                return True
            except queue.Full:
                tmdb_logger.warning("Task queue is full, cannot add new job.")
                with self.movie_lock:
                    self.active_movie_jobs -= 1
                return False

    async def _thread_wrapper(self, coro_func, *args, is_global=False, **kwargs):
        try:
            await coro_func(*args, **kwargs)
        except Exception as e:
            tmdb_logger.error(f"Error in background job: {e}", exc_info=True)
        finally:
            if is_global:
                self.job_running = False
            else:
                with self.movie_lock:
                    self.active_movie_jobs -= 1

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False)
        for _ in range(self.num_workers):
            self.task_queue.put_nowait((None, None, None))

    async def full_sweep(self, first_ingestion: bool) -> None:
        tmdb_logger.info("Running scheduled full sweep...")
        try:
            await update_media_release_webhook_async(
                "**TMDB Service:** Running scheduled full sweep."
            )
            await generate_csvs(first_ingestion)
            # update last full sweep time
            with db() as session:
                set_metadata(
                    session, "last_full_sweep", datetime.now(timezone.utc).isoformat()
                )
                session.commit()
            await update_media_release_webhook_async(
                "**TMDB Service:** Scheduled full sweep completed."
            )
            tmdb_logger.info("Scheduled full sweep completed.")
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            tmdb_logger.error(f"Error in full_sweep: {e}", exc_info=True)
            await update_media_release_webhook_async(
                f"**TMDB Service Error in full_sweep:**  \n```{tb}```"
            )

    async def missing_ids_job(self) -> None:
        tmdb_logger.info("Running missing IDs sweep...")
        try:
            await update_media_release_webhook_async(
                "**TMDB Service:** Running scheduled missing IDs sweep."
            )
            await update_missing_ids()
            await update_media_release_webhook_async(
                "**TMDB Service:** Scheduled missing IDs sweep completed."
            )
            tmdb_logger.info("Missing IDs sweep completed.")
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            tmdb_logger.error(f"Error in missing IDs sweep: {e}", exc_info=True)
            await update_media_release_webhook_async(
                f"**TMDB Service Error in missing IDs sweep:**  \n```{tb}```"
            )

    async def add_movie_id(self, tmdb_id: int) -> None:
        tmdb_logger.info(f"Adding movie ID {tmdb_id}...")
        try:
            await ingest_single_movie(tmdb_id)
            tmdb_logger.info(f"Movie {tmdb_id} ingested.")
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            tmdb_logger.error(f"Error adding movie ID {tmdb_id}: {e}", exc_info=True)
            await update_media_release_webhook_async(
                f"**TMDB Service Error adding movie ID {tmdb_id}:**  \n```{tb}```"
            )

    async def add_series_id(self, tmdb_id: int) -> None:
        tmdb_logger.info(f"Adding series ID {tmdb_id}...")
        try:
            await ingest_single_series(tmdb_id)
            tmdb_logger.info(f"Series {tmdb_id} ingested.")
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            tmdb_logger.error(f"Error adding series ID {tmdb_id}: {e}", exc_info=True)
            await update_media_release_webhook_async(
                f"**TMDB Service Error adding series ID {tmdb_id}:**  \n```{tb}```"
            )

    async def prune_job(self) -> None:
        tmdb_logger.info("Running prune job...")
        try:
            await update_media_release_webhook_async(
                "**TMDB Service:** Running scheduled prune task."
            )
            await prune_deleted_records()
            await update_media_release_webhook_async(
                "**TMDB Service:** Scheduled prune task completed."
            )
            tmdb_logger.info("Prune job completed.")
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            tmdb_logger.error(f"Error in prune job: {e}", exc_info=True)
            await update_media_release_webhook_async(
                f"**TMDB Service Error in prune job:**  \n```{tb}```"
            )

    async def changes_sync_job(self):
        tmdb_logger.info("Running daily TMDB changes sync...")

        # check to ensure we just didn't run the last full sweep task in the last 24 hours
        with db() as session:
            last_full = get_metadata(session, "last_full_sweep")
        if last_full:
            last_full_dt = datetime.fromisoformat(last_full)
            if (datetime.now(timezone.utc) - last_full_dt) < timedelta(hours=24):
                tmdb_logger.info(
                    "Skipping daily TMDB changes sync: Full Sweep ran within the last 24 hours."
                )
                return

        # execute task
        try:
            await process_tmdb_changes_sync()
            await update_media_release_webhook_async(
                "**TMDB Service:** Daily TMDB sync task completed."
            )
            tmdb_logger.info("Daily TMDB sync task completed.")
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            tmdb_logger.error(f"Error in daily TMDB sync task: {e}", exc_info=True)
            await update_media_release_webhook_async(
                f"**TMDB Service Error in daily TMDB sync task:**  \n```{tb}```"
            )

    async def create_db_tables(self) -> None:
        tmdb_logger.info("Creating tables.")
        try:
            create_tables()
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            tmdb_logger.error(f"Error creating tables: {e}", exc_info=True)
            await update_media_release_webhook_async(
                f"**TMDB Service Error creating tables:**  \n```{tb}```"
            )

    def apply_unaccent(self) -> None:
        if global_config.ENABLE_UNACCENT:
            tmdb_logger.info("Adding extension unaccent if not added already.")
            with db_engine.begin() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))

    def init_cron_jobs(self) -> None:
        tmdb_logger.info("Starting TMDB Service.")
        tmdb_logger.info("Creating tables if needed.")
        create_tables()
        cron_jobs = {
            "Full Sweep": (global_config.CRON_FULL_SWEEP, self.full_sweep),
            "Missing IDs": (global_config.CRON_MISSING_ONLY, self.missing_ids_job),
            "Prune Job": (global_config.CRON_PRUNE, self.prune_job),
            "Changes Sync": (global_config.CRON_CHANGES_SYNC, self.changes_sync_job),
        }
        disabled = {"", "false", "off", "disable", "disabled", "no"}
        for k, (vc, vf) in cron_jobs.items():
            if vc.lower() not in disabled:
                try:
                    # checking for errors in CRON before sending it to aiocron.crontab
                    CronSim(vc, datetime.now(timezone.utc))
                    aiocron.crontab(vc)(partial(self.run_global_task_in_thread, vf))
                    tmdb_logger.info(f"Scheduled task '{k}' (CRON: {vc}) successfully.")
                except Exception as e:
                    tmdb_logger.error(
                        f"Failed to schedule task '{k}' (CRON: {vc}). Error: {e}."
                    )
