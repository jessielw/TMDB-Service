#!/bin/sh
set -eu

python -m tmdb_service.migrate
exec "$@"
