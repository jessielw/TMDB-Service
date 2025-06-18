import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def check_truthy(input_value: Any) -> bool:
    return bool(input_value and str(input_value).strip().upper() == "TRUE")


class Config:
    __slots__ = ()

    load_dotenv()
    base_dir = Path.cwd()

    # ensure we're in a container
    if str(base_dir) == "/code" and check_truthy(os.environ.get("in_docker")):
        temp_working_dir = Path("/temp_dir")
        logs = Path("/logs")
    else:
        raise ValueError("Dev only in docker!")

    # create needed directories
    temp_working_dir.mkdir(exist_ok=True)
    logs.mkdir(exist_ok=True)

    # database
    DATABASE_URI = str(os.environ["DATABASE_URI"]).strip()

    # unaccent
    ENABLE_UNACCENT = check_truthy(os.environ.get("ENABLE_UNACCENT"))

    # cron jobs
    CRON_FULL_SWEEP = str(os.environ["CRON_FULL_SWEEP"]).strip()
    CRON_MISSING_ONLY = str(os.environ["CRON_MISSING_ONLY"]).strip()
    CRON_PRUNE = str(os.environ["CRON_PRUNE"]).strip()
    CRON_CHANGES_SYNC = str(os.environ["CRON_CHANGES_SYNC"]).strip()

    # logging
    LOG_TO_CONSOLE = check_truthy(os.environ.get("LOG_TO_CONSOLE"))
    LOG_LVL = int(os.environ.get("LOG_LVL", 20))

    # tmdb
    TMDB_READ_ACCESS_TOKEN = str(os.environ["TMDB_READ_ACCESS_TOKEN"]).strip()
    TMDB_RATE_LIMIT = int(os.environ["TMDB_RATE_LIMIT"])
    TMDB_MAX_CONNECTIONS = int(os.environ["TMDB_MAX_CONNECTIONS"])
    TMDB_BATCH_INSERT = int(os.environ.get("TMDB_BATCH_INSERT", 5000))

    # maubot webhook url
    WEBHOOK_ENABLED = check_truthy(os.environ.get("WEBHOOK_ENABLED"))
    WEBHOOK_BOT_USR = os.environ.get("WEBHOOK_BOT_USR")
    WEBHOOK_BOT_PW = os.environ.get("WEBHOOK_BOT_PW")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
