import select
from typing import Any

import psycopg2

from tmdb_service.globals import tmdb_logger
from tmdb_service.job_queue import get_conn
from tmdb_service.service import TMDBService


JOB_QUEUE_TABLE_SQL = """\
DROP TABLE IF EXISTS job_queue;

CREATE TABLE IF NOT EXISTS job_queue (
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

DROP TRIGGER IF EXISTS job_insert_notify ON job_queue;
CREATE TRIGGER job_insert_notify
AFTER INSERT ON job_queue
FOR EACH ROW EXECUTE FUNCTION notify_new_job();"""


def process_job(job_type: str, payload: Any, service: TMDBService) -> None:
    """Process jobs using TMDBService."""
    if job_type == "full_sweep":
        force = payload in ("True", "true", True)
        service.run_global_task_in_thread(service.full_sweep, first_ingestion=force)
    elif job_type == "missing_ids":
        service.run_global_task_in_thread(service.missing_ids_job)
    elif job_type == "prune_deleted":
        service.run_global_task_in_thread(service.prune_job)
    elif job_type == "changes_sync":
        service.run_global_task_in_thread(service.changes_sync_job)
    elif job_type == "create_tables":
        service.run_single_task_in_thread(service.create_db_tables)
    elif job_type == "add_movie":
        service.run_single_task_in_thread(service.add_movie_id, int(payload))
    elif job_type == "add_series":
        service.run_single_task_in_thread(service.add_series_id, int(payload))
    else:
        tmdb_logger.warning(f"Ignoring unknown job: {job_type}.")


def init_job_queue_table(conn) -> None:
    """Ensure job queue table and trigger exist"""
    with conn.cursor() as cur:
        cur.execute(JOB_QUEUE_TABLE_SQL)
        conn.commit()


def main() -> None:
    tmdb_logger.info("Starting TMDB Worker Service.")
    service = TMDBService()
    service.apply_unaccent()
    service.init_cron_jobs()
    conn = get_conn()
    init_job_queue_table(conn)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("LISTEN new_job;")
    tmdb_logger.info("Listening for new jobs...")

    try:
        while True:
            if select.select([conn], [], [], 5) == ([], [], []):
                continue  # timeout, loop again
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                job_id = int(notify.payload)

                # fetch and delete the job atomically
                cur.execute(
                    "DELETE FROM job_queue WHERE id=%s RETURNING job_type, payload",
                    (job_id,),
                )
                row = cur.fetchone()
                conn.commit()
                if row:
                    job_type, payload = row
                    process_job(job_type, payload, service)
    except KeyboardInterrupt:
        tmdb_logger.info("Shutting down TMDB Worker Service.")
        service.shutdown()


if __name__ == "__main__":
    main()
