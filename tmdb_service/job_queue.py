from typing import Any

import psycopg2

from tmdb_service.globals import global_config


def get_conn():
    return psycopg2.connect(global_config.DATABASE_URI)


def enqueue_job(job_type: str, payload: Any = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO job_queue (job_type, payload) VALUES (%s, %s)",
                (job_type, payload),
            )
