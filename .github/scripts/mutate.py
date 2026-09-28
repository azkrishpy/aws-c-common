#!/usr/bin/env python3
"""Apply one textual mutation to a file. Used by the selftest's mutation check.

    mutate.py <file> <old> <new>

Exits 2 if <old> is absent, so a mutation that has drifted out of date is
reported as broken rather than silently counting as a surviving mutant.
"""
import pathlib
import sys

path, old, new = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
s = path.read_text()
if old not in s:
    print(f"mutation target absent: {old!r}", file=sys.stderr)
    sys.exit(2)
path.write_text(s.replace(old, new, 1))
