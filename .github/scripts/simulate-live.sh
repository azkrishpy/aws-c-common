#!/usr/bin/env bash
# Replay a release history as real git commits, using only the real scripts.
#
# One commit per merged pull request, one per release, dates walking up to today,
# and a docs branch updated after every merge by docs-replay.sh -- the same file
# CI runs. Nothing here writes markdown, moves a directory, or invents a
# changelog: if the result is wrong, the tool is wrong.
#
# Creates NO tag, NO release, NO artifact, and touches nothing outside the two
# local branches it builds.
#
#   simulate-live.sh <sim-branch> <docs-branch> <base-ref> <tooling-ref>
#
# <tooling-ref> holds .github/scripts; the simulated branches carry only the
# history, so their diff against the base is the changelog and nothing else.
set -euo pipefail

SIM="${1:?sim branch}"
DOCS="${2:?docs branch}"
BASE="${3:?base ref}"
TOOLING="${4:?ref holding .github/scripts}"

BIN="$(mktemp -d)"
for f in changelog.py docs-replay.sh; do
  git show "${TOOLING}:.github/scripts/${f}" > "${BIN}/${f}"
done
chmod +x "${BIN}"/*
CL="${BIN}/changelog.py"

git checkout -q -B "$SIM" "$BASE"
git branch -qD "$DOCS" 2>/dev/null || true

commit() {   # commit <days-ago> <message>
  local when
  when="$(date -u -d "-$1 days" +%Y-%m-%dT12:00:00Z)"
  GIT_AUTHOR_DATE="$when" GIT_COMMITTER_DATE="$when" \
    git commit -q --author="aws-sdk-common-runtime-bot <aws-sdk-common-runtime@amazon.com>" -m "$2"
}

replay() {   # mirror the merge onto the docs branch, exactly as CI does
  local head sha
  head="$(git rev-parse --abbrev-ref HEAD)"
  sha="$(git rev-parse HEAD)"
  TRIGGER_SHA="$sha" DEFAULT_BRANCH="$SIM" DOCS_BRANCH="$DOCS" PUSH=false \
    CHANGELOG_PY="$CL" bash "${BIN}/docs-replay.sh" >/dev/null
  git checkout -q "$head"
}

merge_pr() { # merge_pr <days-ago> <pr> <type> <summary> [notes]
  local ago="$1" pr="$2" typ="$3" summary="$4" notes="${5:-}"
  python3 "$CL" seed --pr "$pr" --title "${typ}: ${summary}" \
    --url "https://github.com/azkrishpy/aws-c-common/pull/${pr}" \
    --changes-dir .changes >/dev/null
  if [[ -n "$notes" ]]; then
    python3 - "$pr" "$notes" <<'PY'
import json, pathlib, sys
p = pathlib.Path(f".changes/preview/{sys.argv[1]}.json")
d = json.loads(p.read_text()); d["notes"] = sys.argv[2]
p.write_text(json.dumps(d, indent=2) + "\n")
PY
  fi
  git add .changes
  commit "$ago" "${typ}: ${summary} (#${pr})"
  replay
}

release() {  # release <days-ago> <version> <highlights> <minor-prs>
  local ago="$1" version="$2" highlights="$3" minor="$4"
  local argv=(rollup --version "$version" --date "$(date -u -d "-${ago} days" +%Y-%m-%d)"
              --changes-dir .changes --changelog CHANGELOG.md --docs-branch "$DOCS")
  [[ -n "$highlights" ]] && argv+=(--highlights "$highlights")
  [[ -n "$minor" ]] && argv+=(--minor-prs "$minor")
  python3 "$CL" "${argv[@]}"
  git add -A .changes CHANGELOG.md
  commit "$ago" "chore(release): ${version}"
  replay
}

# ---- adoption: bring the pre-existing tree up to the current rules ----------
python3 - <<'PY'
import json, pathlib
p = pathlib.Path(".changes/latest/0.16.1/22.json")
if p.exists():
    d = json.loads(p.read_text())
    if d.get("type") not in ("feat", "fix", "chore", "revert"):
        d["type"] = "chore"
        p.write_text(json.dumps(d, indent=2) + "\n")
PY
git rm -r -q --cached .changes/0.15.x/0.15.0 .changes/0.15.x/0.15.1 .changes/0.15.x/0.15.2 2>/dev/null || true
rm -rf .changes/0.15.x/0.15.0 .changes/0.15.x/0.15.1 .changes/0.15.x/0.15.2
git add -A .changes
commit 56 "chore: adopt the changelog fragment rules

Documentation is a chore now, so #22 is retyped. A frozen line keeps only its
rendered snapshot; git history still has the fragments."
replay

# ---- the history -----------------------------------------------------------
merge_pr 54 25 feat "Add aws_ring_buffer for zero-copy IO"
merge_pr 52 26 fix  "Correct the byte-buf append bounds check"
merge_pr 50 27 chore "Bump the CI container image"
release  49 0.16.2 "Ring buffer and a bounds fix" ""

merge_pr 46 28 fix  "Handle EINTR in the pipe read loop"
release  45 0.16.3 "" ""

merge_pr 42 29 feat "Add tcp_nodelay to aws_socket_options" \
  "aws_socket_options grew from 40 to 44 bytes. Source-compatible, but a native
consumer that embeds the struct must be rebuilt."
merge_pr 40 30 fix  "Retry backoff off-by-one"
merge_pr 38 31 chore "Document the thread-safety of aws_mutex"
release  37 0.17.0 "Socket options grew a field" "29"

merge_pr 34 32 revert "Reverted the retry-default change" \
  "It changed behaviour customers relied on. A replacement lands in 0.18."
release  33 0.17.1 "" ""

merge_pr 30 33 chore "Update the copyright headers"
release  29 0.17.2 "" ""

merge_pr 26 34 feat "Replace the event-loop dispatch queue" \
  "The old aws_event_loop_vtable layout is gone. Implementers of a custom event
loop must adopt the new vtable."
merge_pr 24 35 feat "Add aws_uuid_to_compact_str"
merge_pr 22 36 fix  "Null-deref in the event loop on shutdown"
release  21 0.18.0 "Event loop rewrite" "34"

merge_pr 18 37 fix  "Leaking fd on socket teardown"
merge_pr 16 38 chore "Bump aws-lc to 1.34"
release  15 0.18.1 "" ""

merge_pr  8 39 feat "Add aws_byte_cursor_split"
merge_pr  5 40 fix  "Guard against a zero-length hash"
merge_pr  2 41 chore "Tidy the CMake feature checks"

echo
echo "sim branch  ${SIM}:  $(git rev-list --count "${BASE}..${SIM}") commits on ${BASE}"
echo "docs branch ${DOCS}: $(git rev-list --count "${BASE}..${DOCS}") commits"
echo "no tag, no release, no artifact created"
