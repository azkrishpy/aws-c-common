#!/usr/bin/env python3
"""Replay a realistic release history and measure what it costs the repository.

Shaped on aws-c-common's actual history (213 releases across 14 minor lines,
median 10 patches per line, busiest 69) so the numbers mean something.

There is nothing to measure under .changes/ any more: a fragment is deleted once
rendered, so the directory holds only what has not shipped. What grows is
CHANGELOG.md, exactly as a hand-written changelog would.

Writes nothing outside a scratch directory.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
CHANGELOG_PY = HERE / "changelog.py"

# (minor, patch count) -- aws-c-common's real distribution, oldest first, run as
# 1.x upward since nothing before 1.0.0 has fragments.
HISTORY = [(1, 5), (2, 8), (3, 16), (4, 69), (5, 10), (6, 21), (7, 13),
           (8, 24), (9, 32), (10, 4), (11, 2), (12, 3), (13, 4), (14, 2)]
PRS_PER_RELEASE = 4


def sh(*args):
    r = subprocess.run([sys.executable, str(CHANGELOG_PY), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr, file=sys.stderr)
        raise SystemExit(f"rollup failed: {' '.join(args)}")


def main():
    work = pathlib.Path(tempfile.mkdtemp())
    changes = work / ".changes"
    changelog = work / "CHANGELOG.md"
    (changes / "preview").mkdir(parents=True)

    pr = releases = 0
    for minor, patches in HISTORY:
        for patch in range(patches):
            for _ in range(PRS_PER_RELEASE):
                pr += 1
                (changes / "preview" / f"{pr}.json").write_text(json.dumps({
                    "pr": pr,
                    "type": ("feat", "fix", "fix", "chore")[pr % 4],
                    "summary": f"Change number {pr} in a realistic release",
                    "notes": "",
                }, indent=2) + "\n")
            sh("rollup", "--version", f"1.{minor}.{patch}", "--date", "2026-01-01",
               "--changes-dir", str(changes), "--changelog", str(changelog))
            releases += 1

    files = [p for p in changes.rglob("*") if p.is_file()]
    text = changelog.read_text()
    print(f"replayed {releases} releases, {pr} pull requests "
          f"({PRS_PER_RELEASE} per release)\n")
    print(f"{'files under .changes/':24} {len(files):>8}")
    print(f"{'bytes under .changes/':24} {sum(p.stat().st_size for p in files):>8,}")
    print(f"{'CHANGELOG.md lines':24} {len(text.splitlines()):>8,}")
    print(f"{'CHANGELOG.md bytes':24} {len(text.encode()):>8,}")
    print(f"{'sections rendered':24} {text.count('## ['):>8}")
    shutil.rmtree(work)


if __name__ == "__main__":
    main()
