# Changelog

<!-- changelog:unreleased -->
## [Unreleased]

### Features
- Add tcp_nodelay to aws_socket_options. ([#1286](../../pull/1286))

### Fixes
- Retry backoff off-by-one. ([#1287](../../pull/1287))

### Notes
- [#1286](../../pull/1286) — aws_socket_options grew from 40 to 44 bytes. Source-compatible, but a native
  consumer that embeds the struct must be rebuilt.
<!-- /changelog:unreleased -->

## [1.0.2] — 2026-09-07

### Features
- Add aws_byte_cursor_split for zero-copy tokenising. ([#1283](../../pull/1283))

### Fixes
- Correct the byte-buf append bounds check. ([#1284](../../pull/1284))

## [1.0.0]

Official release of 1.0.0.
