# Changelog

## [0.15.1] — 2026-08-31
Highlights: Hash table double-free fix.

### Fixes
- Avoid double free in hash table cleanup. (#14)

### Docs
- Document thread-safety of aws_mutex. (#15)

## [0.15.0] — 2026-08-31
Highlights: Ring buffer utility.

### Features
- Add ring buffer utility. (#12)

### Fixes
- Correct byte-buf append bounds check. (#13)
