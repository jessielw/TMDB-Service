#!/usr/bin/env python3

import argparse

from tmdb_service.job_queue import enqueue_job


def main() -> None:
    parser = argparse.ArgumentParser(description="Enqueue TMDB jobs")
    parser.add_argument(
        "job_type",
        choices=(
            "full_sweep",
            "missing_ids",
            "prune_deleted",
            "changes_sync",
            "create_tables",
            "add_movie",
            "add_series",
        ),
        help="Type of job to enqueue",
    )
    parser.add_argument("--id", type=int, help="TMDB ID for add_movie/add_series")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force full sweep regardless of row counts.",
    )

    args = parser.parse_args()

    if args.job_type in ("add_movie", "add_series"):
        if not args.id:
            parser.error("--id is required for add_movie/add_series")
        enqueue_job(args.job_type, str(args.id))
    elif args.job_type == "full_sweep":
        enqueue_job(args.job_type, args.force)
    else:
        enqueue_job(args.job_type)


if __name__ == "__main__":
    main()
