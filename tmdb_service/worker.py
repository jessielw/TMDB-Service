import asyncio
import select
import threading
from collections.abc import Callable
from functools import partial
from typing import Any

import psycopg2

from tmdb_service.globals import tmdb_logger
from tmdb_service.job_queue import (
    claim_next_job,
    complete_job,
    fail_job,
    get_conn,
    requeue_interrupted_jobs,
    requeue_job,
)
from tmdb_service.service import TMDBService


def process_job(
    job_type: str,
    payload: Any,
    service: TMDBService,
    completion_callback: Callable[[Exception | None], None],
) -> bool:
    """Process jobs using TMDBService."""
    if job_type == "full_sweep":
        force = payload in ("True", "true", True)
        return service.run_global_task_in_thread(
            service.full_sweep,
            first_ingestion=force,
            completion_callback=completion_callback,
            notify_on_reject=False,
        )
    elif job_type == "missing_ids":
        return service.run_global_task_in_thread(
            service.missing_ids_job,
            completion_callback=completion_callback,
            notify_on_reject=False,
        )
    elif job_type == "prune_deleted":
        return service.run_global_task_in_thread(
            service.prune_job,
            completion_callback=completion_callback,
            notify_on_reject=False,
        )
    elif job_type == "changes_sync":
        return service.run_global_task_in_thread(
            service.changes_sync_job,
            completion_callback=completion_callback,
            notify_on_reject=False,
        )
    elif job_type == "add_movie":
        return service.run_single_task_in_thread(
            service.add_movie_id,
            int(payload),
            completion_callback=completion_callback,
        )
    elif job_type == "add_series":
        return service.run_single_task_in_thread(
            service.add_series_id,
            int(payload),
            completion_callback=completion_callback,
        )
    elif job_type == "test_webhook":
        return service.run_single_task_in_thread(
            service.test_webhook, payload, completion_callback=completion_callback
        )
    raise ValueError(f"Unknown job type: {job_type}.")


def finalize_job(job_id: int, error: Exception | None) -> None:
    """Persist the outcome reported by a service worker thread."""
    try:
        if error is None:
            complete_job(job_id)
            tmdb_logger.info(f"Job {job_id} completed and was acknowledged.")
        else:
            fail_job(job_id, error)
            tmdb_logger.error(f"Job {job_id} failed and was retained for inspection.")
    except Exception:
        tmdb_logger.exception(f"Unable to persist completion state for job {job_id}.")


def dispatch_queued_jobs(conn, service: TMDBService) -> None:
    """Dispatch queued jobs until the service is busy or the queue is empty."""
    while row := claim_next_job(conn):
        job_id, job_type, payload = row
        callback = partial(finalize_job, job_id)
        try:
            accepted = process_job(job_type, payload, service, callback)
        except Exception as error:
            tmdb_logger.error(
                f"Unable to dispatch job {job_id}: {error}", exc_info=True
            )
            fail_job(job_id, error)
            continue

        if not accepted:
            requeue_job(job_id)
            tmdb_logger.info(
                f"Job {job_id} could not start yet and was returned to the queue."
            )
            return


def main() -> None:
    tmdb_logger.info("Starting TMDB Worker Service.")
    service = TMDBService()
    service.apply_unaccent()

    conn = get_conn()
    interrupted_jobs = requeue_interrupted_jobs(conn)
    if interrupted_jobs:
        tmdb_logger.warning(
            f"Requeued {interrupted_jobs} job(s) interrupted by the previous worker."
        )

    # aiocron binds jobs to the current event loop when they are scheduled. Run that
    # loop in a dedicated thread while this thread blocks waiting for database jobs.
    cron_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(cron_loop)
    service.init_cron_jobs()
    cron_thread = threading.Thread(target=cron_loop.run_forever, daemon=True)
    cron_thread.start()

    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("LISTEN new_job;")
    tmdb_logger.info("Listening for new jobs...")
    dispatch_queued_jobs(conn, service)

    try:
        while True:
            if select.select([conn], [], [], 5) != ([], [], []):
                conn.poll()
                conn.notifies.clear()
            dispatch_queued_jobs(conn, service)
    except KeyboardInterrupt:
        tmdb_logger.info("Shutting down TMDB Worker Service.")
        cron_loop.call_soon_threadsafe(cron_loop.stop)
        cron_thread.join(timeout=5)
        cron_loop.close()
        service.shutdown()


if __name__ == "__main__":
    main()
