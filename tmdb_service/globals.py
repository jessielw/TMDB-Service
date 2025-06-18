import logging

from tmdb_service.config import Config
from tmdb_service.db_utils import get_db
from tmdb_service.logger_utils import init_logger

# config
global_config = Config()

# database
db, Base, db_engine = get_db(global_config.DATABASE_URI)

# logger
tmdb_logger = logging.getLogger("tmdb")
init_logger(
    tmdb_logger,
    global_config.logs,
    "tmdb_service.log",
    log_level=global_config.LOG_LVL,
    log_to_console=global_config.LOG_TO_CONSOLE,
)
