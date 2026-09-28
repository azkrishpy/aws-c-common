#!/usr/bin/env python3
"""Replay a realistic release history through rollup and measure what .changes/ costs.

Shaped on aws-c-common's actual history (213 releases across 14 minor lines,
median 10 patches per line, busiest 69) so the numbers mean something. Compares
the per-PR-file layout this tool uses against the aws-sdk-java-v2 layout, which
collapses each released version into a single JSON.

    rollup-scale.py [--prs-per-release N] [--out DIR]

Writes nothing outside a scratch directory.
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
CHANGELOG_PY = HERE / "changelog.py"

# (minor, patch count) -- aws-c-common's real distribution, oldest first.
HISTORY = [(1, 5), (2, 8), (3, 16), (4, 69), (5, 10), (6, 21), (7, 13),
           (8, 24), (9, 32), (10, 4), (11, 2), (12, 3), (13, 4), (14, 2)]


def sh(*args):
    r = subprocess.run([sys.executable, str(CHANGELOG_PY), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr, file=sys.stderr)
        raise SystemExit(f"rollup failed: {' '.join(args)}")
    return r


def tree_cost(root):
    files = [p for p in root.rglob("*") if p.is_file()]
    dirs = [p for p in root.rglob("*") if p.is_dir()]
    return {
        "files": len(files),
        "dirs": len(dirs),
        "bytes": sum(p.stat().st_size for p in files),
        "json_files": len([p for p in files if p.suffix == ".json"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prs-per-release", type=int, default=4)
    ap.add_argument("--out")
    args = ap.parse_args()

    work = pathlib.Path(args.out) if args.out else pathlib.Path(tempfile.mkdtemp())
    changes = work / ".changes"
    changelog = work / "CHANGELOG.md"
    (changes / "preview").mkdir(parents=True, exist_ok=True)

    pr = 0
    releases = 0
    per_release_entries = []
    for minor, patches in HISTORY:
        for patch in range(patches):
            n = args.prs_per_release
            for _ in range(n):
                pr += 1
                typ = ("feat", "fix", "fix", "chore")[pr % 4]
                (changes / "preview" / f"{pr}.json").write_text(json.dumps({
                    "pr": pr, "type": typ,
                    "summary": f"Change number {pr} in a realistic release",
                    "url": f"https://github.com/azkrishpy/aws-c-common/pull/{pr}",
                    "notes": "",
                }, indent=2) + "\n")
            per_release_entries.append(n)
            sh("rollup", "--version", f"0.{minor}.{patch}",
               "--date", "2026-01-01", "--changes-dir", str(changes),
               "--changelog", str(changelog))
            releases += 1

    ours = tree_cost(changes)
    # The java-v2 layout: one JSON per released version, holding every entry.
    java_files = releases + len(HISTORY)          # version files + per-line dirs' contents
    java_bytes = sum(200 + 160 * e for e in per_release_entries)

    root = changelog.read_text()
    earlier = root.count("- [0.")

    print(f"replayed {releases} releases across {len(HISTORY)} minor lines, "
          f"{pr} PRs ({args.prs_per_release} per release)\n")
    print(f"{'':22} {'this tool':>12} {'java-v2 shape':>14}")
    print(f"{'files under .changes/':22} {ours['files']:>12} {java_files:>14}")
    print(f"{'  of which JSON':22} {ours['json_files']:>12} {releases:>14}")
    print(f"{'directories':22} {ours['dirs']:>12} {len(HISTORY):>14}")
    print(f"{'bytes':22} {ours['bytes']:>12,} {java_bytes:>14,}")
    print(f"\nroot CHANGELOG.md: {len(root.splitlines())} lines, "
          f"{earlier} 'Earlier releases' links")
    print(f"frozen snapshots: {len(list(changes.glob('*.x/CHANGELOG.md')))}")
    biggest = max(changes.glob("*.x"), key=lambda d: len(list(d.rglob('*.json'))))
    print(f"biggest frozen line: {biggest.name} with "
          f"{len(list(biggest.rglob('*.json')))} JSON files in "
          f"{len(list(p for p in biggest.iterdir() if p.is_dir()))} version dirs")
    if not args.out:
        shutil.rmtree(work)


if __name__ == "__main__":
    main()
