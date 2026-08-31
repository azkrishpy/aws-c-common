# Changelog

<!-- changelog:preview:start -->
## [Preview]

### Features
- Add aws_array_list_swap helper. (#18)

### Fixes
- Handle EINTR in pipe read loop. (#17)
- Zero-init allocator vtable padding. (#19)
<!-- changelog:preview:end -->

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
