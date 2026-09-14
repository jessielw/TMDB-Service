from typing import Any

import psycopg2

from tmdb_service.globals import global_config, tmdb_logger

JOB_QUEUE_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS job_queue (
    id SERIAL PRIMARY KEY,
    job_type TEXT NOT NULL,
    payload TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    last_error TEXT
);

ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'queued';
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ;
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS last_error TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'job_queue_status_check'
          AND conrelid = 'job_queue'::regclass
    ) THEN
        ALTER TABLE job_queue
            ADD CONSTRAINT job_queue_status_check
            CHECK (status IN ('queued', 'running', 'failed'));
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS job_queue_status_created_idx
    ON job_queue (status, created_at, id);

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


def get_conn():
    return psycopg2.connect(global_config.DATABASE_URI)


def init_job_queue_table(conn) -> None:
    """Create or migrate the durable job queue schema."""
    with conn.cursor() as cur:
        cur.execute(JOB_QUEUE_TABLE_SQL)
    conn.commit()


def enqueue_job(job_type: str, payload: Any = None) -> int:
    """Add a queued job and return its durable queue ID."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO job_queue (job_type, payload)
                VALUES (%s, %s)
                RETURNING id
                """,
                (job_type, payload),
            )
            return cur.fetchone()[0]


def requeue_interrupted_jobs(conn) -> int:
    """Return jobs left running by a previous worker process to the queue."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE job_queue
            SET status = 'queued', started_at = NULL
            WHERE status = 'running'
            """
        )
        count = cur.rowcount
    conn.commit()
    return count


def claim_next_job(conn) -> tuple[int, str, str | None] | None:
    """Atomically claim the oldest queued job."""
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH next_job AS (
                SELECT id
                FROM job_queue
                WHERE status = 'queued'
                ORDER BY created_at, id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE job_queue AS job
            SET status = 'running',
                started_at = now(),
                finished_at = NULL,
                last_error = NULL,
                attempts = attempts + 1
            FROM next_job
            WHERE job.id = next_job.id
            RETURNING job.id, job.job_type, job.payload
            """
        )
        row = cur.fetchone()
    conn.commit()
    return row


def complete_job(job_id: int) -> None:
    """Acknowledge a successfully completed job and remove it from the queue."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM job_queue WHERE id = %s AND status = 'running'",
                (job_id,),
            )
            if cur.rowcount != 1:
                tmdb_logger.warning(
                    f"Could not acknowledge completed job {job_id}; it was not running."
                )


def fail_job(job_id: int, error: Exception) -> None:
    """Retain a failed job and its error for operator inspection."""
    error_text = f"{type(error).__name__}: {error}"[:4000]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE job_queue
                SET status = 'failed', finished_at = now(), last_error = %s
                WHERE id = %s AND status = 'running'
                """,
                (error_text, job_id),
            )


def requeue_job(job_id: int) -> None:
    """Release a job that could not start because another task is active."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE job_queue
                SET status = 'queued',
                    started_at = NULL,
                    attempts = GREATEST(attempts - 1, 0)
                WHERE id = %s AND status = 'running'
                """,
                (job_id,),
            )
