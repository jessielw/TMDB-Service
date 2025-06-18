import logging
from logging.handlers import WatchedFileHandler
from pathlib import Path


def init_logger(
    lgr: logging.Logger,
    log_dir: Path,
    file_name: str,
    log_level: int = 20,
    log_to_console: bool = True,
):
    """
    Levels: (lvl)
    CRITICAL 50
    ERROR 40
    WARNING 30
    INFO 20
    DEBUG 10
    NOTSET 0
    """
    # set log level
    lgr.setLevel(log_level)

    # format the logger
    formatter = logging.Formatter("%(name)s:%(asctime)s:%(levelname)s = %(message)s")

    # configure WatchedFileHandler for the logger
    file_handler = WatchedFileHandler(log_dir / file_name, mode="a")
    file_handler.setFormatter(formatter)
    lgr.addHandler(file_handler)

    # configure a stream handler for console output if log to console is enabled
    if log_to_console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        lgr.addHandler(stream_handler)

    # disable logger propagation
    lgr.propagate = False

    return lgr
