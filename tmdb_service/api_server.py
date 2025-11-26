#!/usr/bin/env python3
import sys

import uvicorn

from tmdb_service.globals import global_config, tmdb_logger


def main():
    if not global_config.API_ENABLED:
        tmdb_logger.info("API is disabled. Set API_ENABLED=true to enable.")
        sys.exit(0)

    tmdb_logger.info(f"Starting TMDB Service API on port {global_config.API_PORT}")

    if global_config.API_KEY:
        tmdb_logger.info("API key authentication is ENABLED")
    else:
        tmdb_logger.warning(
            "API key authentication is DISABLED. Set API_KEY in .env to secure the API."
        )

    uvicorn.run(
        "tmdb_service.api:app",
        host="0.0.0.0",
        port=global_config.API_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
