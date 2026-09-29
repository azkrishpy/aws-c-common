#!/usr/bin/env python3
"""Replay a realistic release history through rollup and measure what .changes/ costs.

Shaped on aws-c-common's actual history (213 releases across 14 minor lines,
median 10 patches per line, busiest 69) so the numbers mean something.

Reports only what it measures. For comparison, measured from the GitHub API:
aws-sdk-java-v2 keeps 1855 files / 3.83 MB under .changes (one JSON per released
version, retained forever); aws-sdk-go-v2 keeps 1 (released fragments deleted).

Here a released fragment lives in released/ until its minor line closes, at which
point the line collapses to one .md -- so the steady state is "one file per open
pull request, plus one per minor line ever released".

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

# (minor, patch count) -- aws-c-common's real distribution, oldest first. Run as
# 1.x upward, since nothing before 1.0.0 is in the changelog.
HISTORY = [(1, 5), (2, 8), (3, 16), (4, 69), (5, 10), (6, 21), (7, 13),
           (8, 24), (9, 32), (10, 4), (11, 2), (12, 3), (13, 4), (14, 2)]


def sh(*args):
    r = subprocess.run([sys.executable, str(CHANGELOG_PY), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr, file=sys.stderr)
        raise SystemExit(f"rollup failed: {' '.join(args)}")


def tree_cost(root):
    files = [p for p in root.rglob("*") if p.is_file()]
    dirs = [p for p in root.rglob("*") if p.is_dir()]
    return {
        "files": len(files),
        "dirs": len(dirs),
        "bytes": sum(p.stat().st_size for p in files),
        "json_files": len([p for p in files if p.suffix == ".json"]),
    }


PRS_PER_RELEASE = 4


def main():
    work = pathlib.Path(tempfile.mkdtemp())
    changes = work / ".changes"
    changelog = work / "CHANGELOG.md"
    (changes / "preview").mkdir(parents=True, exist_ok=True)

    pr = 0
    releases = 0
    for minor, patches in HISTORY:
        for patch in range(patches):
            for _ in range(PRS_PER_RELEASE):
                pr += 1
                typ = ("feat", "fix", "fix", "chore")[pr % 4]
                (changes / "preview" / f"{pr}.json").write_text(json.dumps({
                    "pr": pr, "type": typ,
                    "summary": f"Change number {pr} in a realistic release",
                    "url": f"https://github.com/azkrishpy/aws-c-common/pull/{pr}",
                    "notes": "",
                }, indent=2) + "\n")
            sh("rollup", "--version", f"1.{minor}.{patch}",
               "--date", "2026-01-01", "--changes-dir", str(changes),
               "--changelog", str(changelog))
            releases += 1

    ours = tree_cost(changes)
    root = changelog.read_text()
    earlier = root.count("- [1.")

    print(f"replayed {releases} releases across {len(HISTORY)} minor lines, "
          f"{pr} PRs ({PRS_PER_RELEASE} per release)\n")
    print(f"{'files under .changes/':22} {ours['files']:>8}")
    print(f"{'  of which JSON':22} {ours['json_files']:>8}")
    print(f"{'directories':22} {ours['dirs']:>8}")
    print(f"{'bytes':22} {ours['bytes']:>8,}")
    print(f"\nroot CHANGELOG.md: {len(root.splitlines())} lines, "
          f"{earlier} 'Earlier releases' links")
    print(f"archived lines: {len(list(changes.glob('*.x.md')))}")
    shutil.rmtree(work)


if __name__ == "__main__":
    main()
