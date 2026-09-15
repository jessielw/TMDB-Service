#!/usr/bin/env python3
import sys

import uvicorn

from tmdb_service.config import api_key_is_secure
from tmdb_service.globals import global_config, tmdb_logger


def main():
    if not global_config.API_ENABLED:
        tmdb_logger.info("API is disabled. Set API_ENABLED=true to enable.")
        sys.exit(0)

    tmdb_logger.info(f"Starting TMDB Service API on port {global_config.API_PORT}")

    if not api_key_is_secure(global_config.API_KEY):
        tmdb_logger.error(
            "API_ENABLED is true but API_KEY is missing or insecure. Refusing to "
            "start. Set a unique API_KEY in .env."
        )
        sys.exit(1)

    tmdb_logger.info("API key authentication is enabled.")

    trusted_proxies = global_config.API_FORWARDED_ALLOW_IPS
    if trusted_proxies == "*":
        tmdb_logger.warning(
            "API_FORWARDED_ALLOW_IPS trusts all peers. Only use '*' when the API is "
            "reachable exclusively through a trusted reverse proxy."
        )

    uvicorn.run(
        "tmdb_service.api:app",
        host="0.0.0.0",
        port=global_config.API_PORT,
        log_level="info",
        proxy_headers=bool(trusted_proxies),
        forwarded_allow_ips=trusted_proxies,
    )


if __name__ == "__main__":
    main()
