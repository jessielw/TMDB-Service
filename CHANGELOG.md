# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-09-14

### Added

- Durable job dispatch.

### Changed

- Global job collisions are dropped rather than deferred.
- Updated all dependencies.

### Fixed

- Service not running at all in some scenarios.
- Cron-fired full sweep dies immediately on a type error.
- Rows silently could go stale.
- The changes-sync watermark was advancing over failed items.
- Chunking was disabled on some high volume points.
- A full sweep that refuses to promote still reported success.
- A transient fetch failure during a full sweep deletes the movie.
- The job queue is dropped on every worker start.
- The full sweep leaked its working directory on failure.
- Deleting a movie behaved differently before and after a full sweep.
-

## [1.1.0] - 2025-11-26

### Added

- Rest API, this can be used for one offs or full control via automation instead of the CRON schedule.
- CLI arg `test_webhook`.

### Fixed

- Issue where external ids would sometimes cause the ingestion for an id to fail.
- **Changes sync** is handled intelligently, it will go as far back as 14 days if needed but will also only pull the last 24 hours if it's been ran sooner.

### Changed

- Some small logging changes.
- Updated numerous dependencies.
