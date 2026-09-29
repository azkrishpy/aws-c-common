#!/usr/bin/env python3
"""Build a browsable release history by driving changelog.py, nothing else.

Every fragment is written by `changelog.py seed`, every release is cut by
`changelog.py rollup`, and every markdown file is whatever those produced. No
step here writes markdown or moves a directory itself -- if the rendered result
is wrong, the tool is wrong, which is the point of looking at it.

    simulate-history.py <target-dir>

Leaves <target-dir>/.changes and <target-dir>/CHANGELOG.md in the state a repo
would be in after the scripted history below.
"""
import json
import pathlib
import subprocess
import sys

CL = pathlib.Path(__file__).resolve().parent / "changelog.py"
REPO = "https://github.com/azkrishpy/aws-c-common"

# (version, highlights, [(type, summary, notes, minor?), ...])
# Three minor lines, several patches each, covering: a minor-labelled entry, a
# revert with notes, a chore that must render nowhere, an empty release, and a
# release whose entries are all chores.
HISTORY = [
    ("0.20.0", "First cut of the new line", [
        ("feat", "Add aws_ring_buffer for zero-copy IO", "", False),
        ("fix", "Correct byte-buf append bounds check", "", False),
        ("chore", "Bump the CI container image", "", False),
    ]),
    ("0.20.1", "", [
        ("fix", "Handle EINTR in the pipe read loop", "", False),
    ]),
    ("0.20.2", "Allocator hardening", [
        ("fix", "Zero-init allocator vtable padding", "", False),
        ("feat", "Add aws_array_list_swap", "", False),
        ("chore", "Document the thread-safety of aws_mutex", "", False),
    ]),
    ("0.21.0", "Socket options grew a field", [
        ("feat", "Add tcp_nodelay to aws_socket_options",
         "aws_socket_options grew from 40 to 44 bytes. Source-compatible, but a\n"
         "native consumer that embeds the struct must be rebuilt.", True),
        ("fix", "Retry backoff off-by-one", "", False),
    ]),
    ("0.21.1", "", [
        ("revert", "Reverted the retry-default change",
         "It changed behaviour customers relied on. A replacement lands in 0.22.",
         False),
    ]),
    ("0.21.2", "", []),
    ("0.21.3", "", [
        ("chore", "Update copyright headers", "", False),
    ]),
    ("0.22.0", "Event loop rewrite", [
        ("feat", "Replace the event-loop dispatch queue",
         "The old aws_event_loop_vtable layout is gone. Implementers of a custom\n"
         "event loop must adopt the new vtable.", True),
        ("feat", "Add aws_uuid_to_compact_str", "", False),
        ("fix", "Null-deref in the event loop on shutdown", "", False),
    ]),
    ("0.22.1", "", [
        ("fix", "Leaking fd on socket teardown", "", False),
        ("chore", "Bump aws-lc to 1.34", "", False),
    ]),
]


def run(*args):
    r = subprocess.run([sys.executable, str(CL), *args], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        raise SystemExit(f"changelog.py {args[0]} failed with {r.returncode}")
    return r


def main():
    root = pathlib.Path(sys.argv[1]).resolve()
    changes, changelog = root / ".changes", root / "CHANGELOG.md"
    (changes / "preview").mkdir(parents=True, exist_ok=True)

    pr = 100
    for version, highlights, entries in HISTORY:
        minor = []
        for typ, summary, notes, is_minor in entries:
            pr += 1
            # The author's path: seed from the PR title, then fill in notes.
            run("seed", "--pr", str(pr), "--title", f"{typ}: {summary}",
                "--url", f"{REPO}/pull/{pr}", "--changes-dir", str(changes))
            if notes:
                frag = changes / "preview" / f"{pr}.json"
                data = json.loads(frag.read_text())
                data["notes"] = notes
                frag.write_text(json.dumps(data, indent=2) + "\n")
            if is_minor:
                minor.append(str(pr))
        argv = ["rollup", "--version", version, "--date", "2026-01-01",
                "--changes-dir", str(changes), "--changelog", str(changelog)]
        if highlights:
            argv += ["--highlights", highlights]
        if minor:
            argv += ["--minor-prs", ",".join(minor)]
        run(*argv)

    # A few merges land after the last release, so preview/ is non-empty -- the
    # state a repo actually sits in most of the time.
    for typ, summary in [("feat", "Add aws_byte_cursor_split"),
                         ("fix", "Guard against a zero-length hash"),
                         ("chore", "Tidy the CMake feature checks")]:
        pr += 1
        run("seed", "--pr", str(pr), "--title", f"{typ}: {summary}",
            "--url", f"{REPO}/pull/{pr}", "--changes-dir", str(changes))

    # The docs-branch view: same tool, preview block included.
    run("render", "--changes-dir", str(changes),
        "--changelog", str(root / "CHANGELOG.docs-branch.md"))
    print(f"\nsimulated {len(HISTORY)} releases, {pr - 100} pull requests")


if __name__ == "__main__":
    main()
