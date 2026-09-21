# Changelog

<!-- changelog:unreleased -->
## [Unreleased]

_Nothing yet._
<!-- /changelog:unreleased -->

## [1.2.0] — 2026-09-21

### Possible Breaking Changes
- Replace the event-loop dispatch queue. ([#1289](../../pull/1289))

### Features
- Add aws_uuid_to_compact_str. ([#1290](../../pull/1290))

### Reverts
- Reverted the retry-default change. ([#1291](../../pull/1291))

### Notes
- [#1289](../../pull/1289) — The old aws_event_loop_vtable layout is gone. Implementers of a custom event
  loop must adopt the new vtable.
- [#1291](../../pull/1291) — It changed behaviour customers relied on. A replacement lands in 1.3.

## Earlier releases

- [1.1.x](.changes/1.1.x.md)
- [1.0.x](.changes/1.0.x.md)
