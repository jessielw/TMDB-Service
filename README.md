# TMDB-Service

Service that Mirrors the [TMDB API](https://developer.themoviedb.org/docs/getting-started) (most of it) to cache locally for use with your own services that need access with quick response times. Setup to work with Postgres. Automatically keeps data 1:1 based on CRON tasks.

### Should You Use This

- You are running a service or application that frequently accesses TMDB data and would benefit from a local cache to improve performance and reduce external API usage.
- You want to minimize your reliance on TMDB’s rate limits or ensure availability during outages.
- You need faster response times or more control over the data retrieval process.

### Who Shouldn't Use This

- If you are just occasionally looking up data you should use [TMDB-API](https://developer.themoviedb.org/docs/getting-started) directly.
- You're only making occasional or infrequent requests to TMDB.
- You're building a simple app, script, or tool that doesn’t need caching or local storage.
- You don’t want to maintain an additional service or deal with syncing data.

---

## ⚡ Quick Start

1. **Get your TMDB API token** from [TMDB Settings](https://www.themoviedb.org/settings/api)

2. **Create a `.env` file** (see [configuration](#-configuration) below)

3. **Start the services:**

   ```bash
   docker compose up -d
   ```

4. **Trigger initial data ingestion:**

   ```bash
   docker compose exec tmdb_service manage_jobs full_sweep --force
   ```

5. **Access your data** via PostgreSQL on `localhost:5432` (or use the optional REST API)

---

## 📦 Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
# Database Configuration
DATABASE_URI='postgresql://tmdb:pw@tmdb_postgres:5432/tmdb'
POSTGRES_USER=tmdb
POSTGRES_PASSWORD='secure-password-here'
POSTGRES_DB=tmdb

# PostgreSQL Extensions
ENABLE_UNACCENT=true  # Improves text search

# TMDB API
TMDB_READ_ACCESS_TOKEN='your-tmdb-read-access-token'
TMDB_RATE_LIMIT=45            # Requests per second (TMDB max is 50)
TMDB_MAX_CONNECTIONS=20       # Concurrent connections (TMDB max is 20)
TMDB_BATCH_INSERT=1000        # Database batch size

# CRON Schedules (standard cron syntax, or 'false' to disable)
CRON_FULL_SWEEP='0 3 13,28 * *'    # Full refresh: 3 AM on 13th & 28th
CRON_MISSING_ONLY='0 6 * * 1'      # Missing IDs: 6 AM Monday
CRON_PRUNE='0 3 19 * *'            # Cleanup: 3 AM on 19th
CRON_CHANGES_SYNC='0 18 * * *'     # Daily sync: 6 PM daily

# Logging
LOG_TO_CONSOLE=true
LOG_LVL=20  # 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR

# Webhooks (Optional - for maubot-webhook)
WEBHOOK_ENABLED=false
WEBHOOK_BOT_USR=maubot
WEBHOOK_BOT_PW=your-webhook-password
WEBHOOK_URL='https://matrix.example.com/_matrix/maubot/plugin/webhook/send'

# REST API (Optional)
API_ENABLED=false
API_PORT=8000
API_KEY=your-secret-api-key-here
```

### 📝 Configuration Details

#### CRON Schedules Explained

**CRON_FULL_SWEEP** - Complete data refresh from TMDB exports

- Downloads entire dataset _(this will take several hours on good internet)_
- Replaces all existing data
- Resource intensive but ensures perfect sync
- Recommended: Once or twice monthly during off-peak hours

**CRON_CHANGES_SYNC** - Incremental daily updates ⭐ **Recommended**

- Syncs only items that changed in last 24 hours
- Lightweight and fast
- Automatically tracks last sync time
- Handles new releases, updates, and deletions
- Skips automatically if full sweep ran within 24h

**CRON_MISSING_ONLY** - Backfill missing IDs

- Finds IDs in TMDB exports that aren't in your database
- Insert-only: existing movie and series rows are not refreshed by this task
- Useful for catching gaps
- Can be disabled if using daily changes sync

**CRON_PRUNE** - Remove deleted content

- Deletes records that no longer exist in TMDB
- Keeps database clean
- Can be disabled if using daily changes sync

#### Disabling CRON Tasks

Set any CRON variable to one of: `""`, `"false"`, `"off"`, `"disable"`, `"disabled"`, or `"no"` (case insensitive)

```env
CRON_PRUNE='false'
CRON_MISSING_ONLY='off'
```

#### Data Freshness and Recovery

- TMDB's changes feeds do not track changes to `popularity`, `vote_average`, or
  `vote_count`. Those fields refresh only during a full sweep and can therefore be as
  old as your `CRON_FULL_SWEEP` interval.
- TMDB permits at most a 14-day changes lookback. If the last successful changes sync
  is older than that, the service logs and sends a webhook warning, then covers the
  available 14 days. Run a forced full sweep to fill the older gap.
- Missing-ID sweeps only insert absent titles; use changes sync or a full sweep to
  refresh titles already in the database.

---

## .env File Example

```
DATABASE_URI='postgresql://tmdb:pw@tmdb_postgres:5432/tmdb'
POSTGRES_USER=tmdb
POSTGRES_PASSWORD='pw'
POSTGRES_DB=tmdb
ENABLE_UNACCENT=true
CRON_FULL_SWEEP='0 3 13,28 * *'
CRON_MISSING_ONLY='0 6 * * 1'
CRON_PRUNE='0 3 19 * *'
CRON_CHANGES_SYNC='0 18 * * *'
LOG_TO_CONSOLE=true
LOG_LVL=20
TMDB_READ_ACCESS_TOKEN='access token'
TMDB_RATE_LIMIT=45
TMDB_MAX_CONNECTIONS=20
TMDB_BATCH_INSERT=1000

# notifications (maubot webhook)
WEBHOOK_ENABLED=true
WEBHOOK_BOT_USR=maubot
WEBHOOK_BOT_PW=SOME_PASSWORD
WEBHOOK_URL='https://matrix.SOME_URL.net/_matrix/maubot/plugin/BOT_URL/send'

# api (optional)
API_ENABLED=true
API_PORT=8000
API_KEY='your-secret-api-key-here'
```

---

## 🌐 HTTP API (Optional)

TMDB-Service includes an optional REST API for programmatic control and integration with external tools.

### Why Use the API?

- **Automation** - Trigger syncs from CI/CD pipelines or other services
- **On-Demand Updates** - Add specific movies/series when users request them
- **Monitoring** - Health checks and status endpoints
- **Integration** - Easy to integrate with webhooks, automation tools, etc.

### Enable the API

Add to your `.env` file:

```env
API_ENABLED=true          # Enable the REST API
API_PORT=8000            # Port (default: 8000)
API_KEY=your-secret-key  # API key for authentication (highly recommended!)
```

> **⚠️ Security Note:** If `API_KEY` is not set, the API is accessible without authentication. Always set an API key for production deployments!

### 📚 Interactive Documentation

Once enabled, explore the full API at:

- **Swagger UI:** `http://localhost:8000/docs` (interactive, try-it-out features)
- **ReDoc:** `http://localhost:8000/redoc` (clean, readable documentation)

### 🔑 Authentication

Include your API key in the `X-API-Key` header with all requests:

```bash
curl -H "X-API-Key: your-secret-key" http://localhost:8000/health
```

### 📡 Available Endpoints

<table>
<tr><th>Category</th><th>Endpoint</th><th>Description</th></tr>

<tr><td rowspan="6"><b>Jobs</b></td>
<td><code>POST /jobs/full-sweep</code></td>
<td>Trigger complete TMDB data refresh</td></tr>

<tr><td><code>POST /jobs/changes-sync</code></td>
<td>Sync recent changes (recommended for daily use)</td></tr>

<tr><td><code>POST /jobs/missing-ids</code></td>
<td>Backfill missing TMDB IDs</td></tr>

<tr><td><code>POST /jobs/prune-deleted</code></td>
<td>Remove records deleted from TMDB</td></tr>

<tr><td><code>POST /jobs/create-tables</code></td>
<td>Initialize database schema</td></tr>

<tr><td><code>POST /jobs/test-webhook</code></td>
<td>Test webhook notifications</td></tr>

<tr><td rowspan="2"><b>Media</b></td>
<td><code>POST /movies/{tmdb_id}</code></td>
<td>Add or update specific movie by ID</td></tr>

<tr><td><code>POST /series/{tmdb_id}</code></td>
<td>Add or update specific TV series by ID</td></tr>

<tr><td rowspan="2"><b>Health</b></td>
<td><code>GET /</code></td>
<td>API service information</td></tr>

<tr><td><code>GET /health</code></td>
<td>Health check endpoint</td></tr>
</table>

### 💡 Example Usage

```bash
# Add a specific movie (Fight Club)
curl -X POST \
  -H "X-API-Key: your-secret-key" \
  http://localhost:8000/movies/550

# Trigger incremental sync
curl -X POST \
  -H "X-API-Key: your-secret-key" \
  http://localhost:8000/jobs/changes-sync

# Full data refresh with force flag
curl -X POST \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"force": true}' \
  http://localhost:8000/jobs/full-sweep

# Test webhook notifications
curl -X POST \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test notification"}' \
  http://localhost:8000/jobs/test-webhook
```

### 🔒 Durable Job Queue

Jobs submitted by cron, the API, and the CLI use the same PostgreSQL-backed queue:

- Queued jobs survive worker restarts.
- Jobs interrupted while running are returned to the queue when the worker starts.
- Jobs that collide with an active global or title task remain queued until capacity is
  available.
- Successfully completed jobs are removed. Failed jobs remain in `job_queue` with
  `status = 'failed'`, an attempt count, and `last_error` for operator inspection.

Direct callers of the in-process global-task dispatcher still receive `False` when the
service is busy; when webhooks are enabled, that rejection sends a notification.

---

## 🖥 CLI Management

The `manage_jobs` CLI provides manual control over all service operations. Execute commands from within the running container:

### Common Commands

```bash
# Add a specific movie
docker compose exec tmdb_service manage_jobs add_movie --id 550

# Add a TV series
docker compose exec tmdb_service manage_jobs add_series --id 1396

# Trigger full sweep (with force flag)
docker compose exec tmdb_service manage_jobs full_sweep --force

# Sync recent changes
docker compose exec tmdb_service manage_jobs changes_sync

# Sync missing IDs
docker compose exec tmdb_service manage_jobs missing_ids

# Remove deleted records
docker compose exec tmdb_service manage_jobs prune_deleted

# Test webhook
docker compose exec tmdb_service manage_jobs test_webhook --message "Test alert"
```

### CLI Reference

```
Usage: manage_jobs [-h] [--id ID] [--force] [--message MESSAGE]
                   {full_sweep,missing_ids,prune_deleted,changes_sync,
                    create_tables,add_movie,add_series,test_webhook}

Options:
  --id ID           TMDB ID for add_movie/add_series
  --force           Force full sweep regardless of existing data
  --message TEXT    Custom message for webhook testing
```

---

## 🗄 Database Backup & Restore

### Backup Database

```bash
docker compose exec tmdb_postgres pg_dump -U tmdb tmdb > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Copy dump to container
docker compose cp backup.sql tmdb_postgres:/tmp/dump.sql

# Drop existing schema
docker compose exec tmdb_postgres psql -U tmdb tmdb -c "DROP SCHEMA public CASCADE;"

# Recreate schema
docker compose exec tmdb_postgres psql -U tmdb tmdb -c "CREATE SCHEMA public;"

# Restore from dump
docker compose exec tmdb_postgres psql -U tmdb tmdb -f /tmp/dump.sql

# Cleanup
docker compose exec tmdb_postgres rm /tmp/dump.sql
```

---

## 🚢 Docker Deployment

### Docker Compose Setup

Create a `docker-compose.yaml` file:

```yaml
services:
  tmdb_postgres:
    image: postgres:16
    container_name: tmdb_postgres
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  tmdb_service:
    image: ghcr.io/jessielw/tmdb-service:latest
    container_name: tmdb_service
    restart: unless-stopped
    depends_on:
      - tmdb_postgres
    env_file:
      - .env
    volumes:
      - ./temp_dir:/temp_dir
      - ./logs:/logs
    command: ["python", "-m", "tmdb_service.worker"]

  # Optional: REST API service
  tmdb_api:
    image: ghcr.io/jessielw/tmdb-service:latest
    container_name: tmdb_api
    restart: on-failure
    depends_on:
      - tmdb_postgres
    env_file:
      - .env
    ports:
      - "${API_PORT:-8000}:${API_PORT:-8000}"
    command: ["python", "-m", "tmdb_service.api_server"]
```

### First Time Setup

1. **Create your `.env` file** (see [Configuration](#-configuration))

2. **Start the services:**

   ```bash
   docker compose up -d

   # Or with API enabled:
   docker compose --profile api up -d
   ```

3. **Trigger initial data ingestion:**

   ```bash
   docker compose exec tmdb_service manage_jobs full_sweep --force
   ```

   This downloads the complete TMDB dataset (10-20 minutes depending on your connection).

4. **Verify the data:**

   ```bash
   # Check database
   docker compose exec tmdb_postgres psql -U tmdb tmdb -c "SELECT COUNT(*) FROM movie;"

   # Check logs
   docker compose logs -f tmdb_service
   ```

### 📁 Required Volumes

| Container       | Mount Point                | Purpose                     |
| --------------- | -------------------------- | --------------------------- |
| `tmdb_postgres` | `/var/lib/postgresql/data` | PostgreSQL data persistence |
| `tmdb_service`  | `/temp_dir`                | Temporary files during sync |
| `tmdb_service`  | `/logs`                    | Application logs            |

### 🔄 Ongoing Maintenance

**Automatic (Recommended):** Configure CRON schedules in your `.env` file for hands-off operation.

**Manual:** Use the [CLI](#-cli-management) or [API](#-http-api-optional) to trigger jobs on-demand.

### 🏗 Building from Source

```bash
# Multi-platform build
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/jessielw/tmdb-service:latest \
  --push .

# Local build
docker build -t tmdb-service:local .
```

---

## Using with Flask and Flask-SQLAlchemy

For convenience I've added **movies.py** and **series.py** models already converted for **Flask-SQLAlchemy** in `examples/flask_sqlalchemy_models/*.py`. You'll need to update `from your_app_service import db` import from your application. However, follow the guide below explaining how you can do this yourself if needed.

Cast character and order belong to the title-person relationship. Read them through
`Movie.cast_roles` / `Series.cast_roles`; each role exposes `character`, `cast_order`,
and `cast_member`. `cast_members` remains as a read-only convenience relationship.
When upgrading from a schema that stored these fields on cast members, the automatic
migration preserves the old values as a best effort. Run one forced full sweep to
reconstruct accurate historical roles for every title.

To integrate TMDB models into your Flask project using **Flask-SQLAlchemy**, the simplest approach is to copy `movies.py` and `series.py` into your project. You’ll need to make a few adjustments for **every model** and **every association table**:

- Add `__bind_key__ = "tmdb"` to each model.
- Add `bind_key="tmdb"` to any `db.Table` association definitions.
- Adjust model inheritance to use your project's `db.Model`.

### Example

```python
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column, relationship

from your_flask_project import db  # use your actual db instance

class MovieCollections(db.Model, MappedAsDataclass): # ➤ New: Change from (Base) to (db.Model, MappedAsDataclass)
    __bind_key__ = "tmdb"  # ➤ New: use the TMDB database bind
    __tablename__ = "movie_collections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(default=None)
    poster_path: Mapped[str | None] = mapped_column(String(255), default=None)
    backdrop_path: Mapped[str | None] = mapped_column(String(255), default=None)

    movies: Mapped[list["Movie"]] = relationship(
        back_populates="belongs_to_collection",
        init=False,
        cascade="all, delete-orphan",
        single_parent=True,
        default_factory=list,
        repr=False,
    )

movie_genres_assoc = db.Table(
    "movie_genres_assoc",
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column("genre_id", ForeignKey("movie_genres.id"), primary_key=True),
    bind_key="tmdb",  # ➤ New: specify bind for the association table
)
```

### Notes

- Adding `__bind_key__ = "tmdb"` tells SQLAlchemy to use the TMDB-specific database connection.
- The TMDB-Service is designed as a **read-only** cache, but nothing stops you from writing to it if needed.
