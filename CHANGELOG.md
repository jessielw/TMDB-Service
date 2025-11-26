# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
