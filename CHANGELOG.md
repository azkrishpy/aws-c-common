# Changelog

<!-- changelog:unreleased -->
## [Unreleased]

### Features
- Replace the event-loop dispatch queue. ([#1289](../../pull/1289))
- Add aws_uuid_to_compact_str. ([#1290](../../pull/1290))

### Reverts
- Reverted the retry-default change. ([#1291](../../pull/1291))

### Notes
- [#1289](../../pull/1289) — The old aws_event_loop_vtable layout is gone. Implementers of a custom event
  loop must adopt the new vtable.
- [#1291](../../pull/1291) — It changed behaviour customers relied on. A replacement lands in 1.3.
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
