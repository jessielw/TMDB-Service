import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def check_truthy(input_value: Any) -> bool:
    return bool(input_value and str(input_value).strip().upper() == "TRUE")


INSECURE_API_KEYS = frozenset({"your-secret-api-key-here"})


def api_key_is_secure(api_key: str | None) -> bool:
    return bool(api_key and api_key not in INSECURE_API_KEYS)


class Config:
    __slots__ = (
        "API_DOCS_ENABLED",
        "API_ENABLED",
        "API_FORWARDED_ALLOW_IPS",
        "API_KEY",
        "API_PORT",
        "API_RATE_LIMIT",
        "CRON_CHANGES_SYNC",
        "CRON_FULL_SWEEP",
        "CRON_MISSING_ONLY",
        "CRON_PRUNE",
        "DATABASE_URI",
        "LOG_LVL",
        "LOG_TO_CONSOLE",
        "TMDB_BATCH_INSERT",
        "TMDB_MAX_CONNECTIONS",
        "TMDB_RATE_LIMIT",
        "TMDB_READ_ACCESS_TOKEN",
        "WEBHOOK_BOT_PW",
        "WEBHOOK_BOT_USR",
        "WEBHOOK_ENABLED",
        "WEBHOOK_URL",
        "base_dir",
        "logs",
        "temp_working_dir",
    )

    def __init__(self) -> None:
        load_dotenv()
        self.base_dir = Path.cwd()

        if self.base_dir == Path("/code") and check_truthy(os.environ.get("in_docker")):
            self.temp_working_dir = Path("/temp_dir")
            self.logs = Path("/logs")
        else:
            raise ValueError("Dev only in docker!")

        self.temp_working_dir.mkdir(exist_ok=True)
        self.logs.mkdir(exist_ok=True)

        self.DATABASE_URI = str(os.environ["DATABASE_URI"]).strip()
        self.CRON_FULL_SWEEP = str(os.environ["CRON_FULL_SWEEP"]).strip()
        self.CRON_MISSING_ONLY = str(os.environ["CRON_MISSING_ONLY"]).strip()
        self.CRON_PRUNE = str(os.environ["CRON_PRUNE"]).strip()
        self.CRON_CHANGES_SYNC = str(os.environ["CRON_CHANGES_SYNC"]).strip()

        self.LOG_TO_CONSOLE = check_truthy(os.environ.get("LOG_TO_CONSOLE"))
        self.LOG_LVL = int(os.environ.get("LOG_LVL", 20))

        self.TMDB_READ_ACCESS_TOKEN = str(os.environ["TMDB_READ_ACCESS_TOKEN"]).strip()
        self.TMDB_RATE_LIMIT = int(os.environ["TMDB_RATE_LIMIT"])
        self.TMDB_MAX_CONNECTIONS = int(os.environ["TMDB_MAX_CONNECTIONS"])
        self.TMDB_BATCH_INSERT = int(os.environ.get("TMDB_BATCH_INSERT", 5000))

        self.WEBHOOK_ENABLED = check_truthy(os.environ.get("WEBHOOK_ENABLED"))
        self.WEBHOOK_BOT_USR = os.environ.get("WEBHOOK_BOT_USR")
        self.WEBHOOK_BOT_PW = os.environ.get("WEBHOOK_BOT_PW")
        self.WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

        self.API_ENABLED = check_truthy(os.environ.get("API_ENABLED"))
        self.API_PORT = int(os.environ.get("API_PORT", 8000))
        self.API_KEY = (os.environ.get("API_KEY") or "").strip() or None
        self.API_DOCS_ENABLED = check_truthy(os.environ.get("API_DOCS_ENABLED"))
        self.API_RATE_LIMIT = (os.environ.get("API_RATE_LIMIT") or "60/minute").strip()
        self.API_FORWARDED_ALLOW_IPS = (
            os.environ.get("API_FORWARDED_ALLOW_IPS") or ""
        ).strip()
