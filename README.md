# TMDB-Service

Service that Mirrors TMDB API (most of it) to cache locally for use with your own services that need access with quick response times. Setup to work with Postgres. Automatically keeps data 1:1 based on CRON tasks.

### Should You Use This

- You are running a service or application that frequently accesses TMDB data and would benefit from a local cache to improve performance and reduce external API usage.
- You want to minimize your reliance on TMDB’s rate limits or ensure availability during outages.
- You need faster response times or more control over the data retrieval process.

### Who Shouldn't Use This

- If you are just occasionally looking up data you should use [TMDB-API](https://developer.themoviedb.org/docs/getting-started) directly.
- You're only making occasional or infrequent requests to TMDB.
- You're building a simple app, script, or tool that doesn’t need caching or local storage.
- You don’t want to maintain an additional service or deal with syncing data.

## .env File Example

```
DATABASE_URI='postgresql://tmdb:pw@tmdb_postgres:5432/tmdb'
POSTGRES_USER=tmdb
POSTGRES_PASSWORD='pw'
POSTGRES_DB=tmdb
ENABLE_UNACCENT=true
CRON_FULL_SWEEP='0 3 15,30 * *'
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
```

### Disable CRON tasks

If you'd like to disable of the **CRON tasks** you can simply pass any of the following **""**, **"false"**, **"off"**, **"disable"**, **"disabled"**, or **"no"** _(case insensitive)_.

`CRON_PRUNE=''`

`CRON_PRUNE='off'`

#### CRON_CHANGES_SYNC

This task will automatically keep your database up to date with the most recent changes from TMDB API in the last 24 hours. You can set this task to when ever you want but it should be ran every **24 hours**. On the day that **CRON_FULL_SWEEP** has ran, this task will be skipped automatically.

### Log Levels

For `LOG_LVL` provide an **integer** for the logging from below (defaults to 20).

```
CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
NOTSET = 0
```

`LOG_LVL=20`

### Webhook

Webhooks will alert you of task completions as well as errors.

_Currently only [maubot-webhook](https://github.com/jkhsjdhjs/maubot-webhook) is supported._

### manage_jobs CLI

While TMDB-Service is meant to be self maintained, there is a convenience CLI to run some basic commands. You must execute this from within running docker container/network.

**Add Movie**:

```
docker compose exec tmdb_service manage_jobs add_movie --id 603
```

**Usage**:

```
usage: manage_jobs [-h] [--id ID] [--force]
                   {full_sweep,missing_ids,prune_deleted,changes_sync,create_tables,add_movie,add_series}

Enqueue TMDB jobs

positional arguments:
  {full_sweep,missing_ids,prune_deleted,changes_sync,create_tables,add_movie,add_series}
                        Type of job to enqueue

options:
  -h, --help            show this help message and exit
  --id ID               TMDB ID for add_movie/add_series
  --force               Force full sweep regardless of row counts.
```

### Build Example

```
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/jessielw/tmdb-service:1.0.0 -t ghcr.io/jessielw/tmdb-service:latest --push .
```

### Backup

```
docker compose exec postgres pg_dump -U tmdb tmdb > /some_path/dump.sql
```

### Restore

```
# copy dump
docker compose cp /some_path/dump.sql tmdb_postgres:/tmp/dump.sql

# clean schema
docker compose exec tmdb_postgres psql -U tmdb tmdb -c "DROP SCHEMA public CASCADE;"

# create schema
docker compose exec tmdb_postgres psql -U tmdb tmdb -c "CREATE SCHEMA public;"

# update database from copied dump
docker compose exec tmdb_postgres psql -U tmdb tmdb -f /tmp/dump.sql

# remove copied dump inside of the container
docker compose exec tmdb_postgres rm /tmp/dump.sql
```

## How To Use

Refer to the [.env example](#env-file-example) for the required environment variables.

### First Time Setup

1. Setup a docker compose file _(You can use a .env file or directly supply environmental variables in your docker run/compose)_.

   ```yaml
   services:
     tmdb_postgres:
       image: postgres:16
       container_name: tmdb_postgres
       restart: unless-stopped
       env_file:
         - .env
       volumes:
         - SOME_PATH:/var/lib/postgresql/data

     tmdb_service:
       image: ghcr.io/jessielw/tmdb-service:latest
       container_name: tmdb_service
       restart: unless-stopped
       depends_on:
         - tmdb_postgres
       env_file:
         - .env
       volumes:
         - SOME_PATH:/temp_dir
         - SOME_PATH:/logs
       networks:
         - proxynet
       command: ["python", "-m", "tmdb_service.worker"]
   ```

2. Start the service.

   `docker compose up` or `docker run ...`

3. Utilize [Manage Jobs CLI](#manage_jobs-cli) to start initial ingestion in another terminal by triggering the **full_sweep**.

   `docker compose exec tmdb_service manage_jobs full_sweep --force`

   This will take some time depending on network conditions.

### Required Volumes

#### tmdb_postgres

```
/somewhere:/var/lib/postgresql/data
```

#### tmdb_service

```
/somewhere/temp:/temp_dir
/somewhere/logs:/logs
```

### Maintaining The Service

This is handled automatically via the CRON tasks (refer to [.env example](#env-file-example)).

_The [example CRON](#env-file-example) schedule should be adequate for most use cases._

`CRON_FULL_SWEEP`: Performs a **complete** re-ingestion of TMDB data from the API, similar to the initial population.

`CRON_MISSING_ONLY`: Ingests only missing IDs based on the most recent full dataset. _(If using `CRON_CHANGES_SYNC` you can disable this)_

`CRON_PRUNE`: Removes any IDs currently in the local cache that no longer exist in the latest full dataset. _(If using `CRON_CHANGES_SYNC` you can disable this)_

`CRON_CHANGES_SYNC`: Should be run approximately every **24 hours** to keep up with incremental changes from TMDB.

You can also utilize [Manage Jobs CLI](#manage_jobs-cli) to run numerous commands without utilizing the **CRON** schedules.
