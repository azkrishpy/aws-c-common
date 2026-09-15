# Changelog

<!-- changelog:unreleased -->
Unreleased changes can be found [here](../../blob/sim-1x-docs/CHANGELOG.md).
<!-- /changelog:unreleased -->

## [1.1.1] — 2026-09-15

### Fixes
- Handle EINTR in the pipe read loop. ([#1288](../../pull/1288))

## [1.1.0] — 2026-09-11

### Possible Breaking Changes
- Add tcp_nodelay to aws_socket_options. ([#1286](../../pull/1286))

### Fixes
- Retry backoff off-by-one. ([#1287](../../pull/1287))

### Notes
- [#1286](../../pull/1286) — aws_socket_options grew from 40 to 44 bytes. Source-compatible, but a native
  consumer that embeds the struct must be rebuilt.

## Earlier releases

- [1.0.x](.changes/1.0.x.md)
