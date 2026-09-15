from typing import Any

import psycopg2

from tmdb_service.globals import global_config, tmdb_logger


def get_conn():
    return psycopg2.connect(global_config.DATABASE_URI)


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
            return cur.fetchone()[0]  # type: ignore[reportOptionalSubscript]


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
