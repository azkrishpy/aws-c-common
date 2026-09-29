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

# docs-replay.sh prefers a remote docs branch when one exists -- correct in
# production, wrong here: a rerun would replay onto a previous run's state and
# conflict. Refuse rather than build a half-stale branch.
if git ls-remote --exit-code --heads origin "$DOCS" >/dev/null 2>&1; then
  echo "ERROR: ${DOCS} exists on origin; a rerun would replay onto it." >&2
  echo "       Delete it first: git push origin --delete ${DOCS}" >&2
  exit 1
fi

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

release() {  # release <days-ago> <version> <minor-prs>
  local ago="$1" version="$2" minor="$3"
  local argv=(rollup --version "$version" --date "$(date -u -d "-${ago} days" +%Y-%m-%d)"
              --changes-dir .changes --changelog CHANGELOG.md --docs-branch "$DOCS")
  [[ -n "$minor" ]] && argv+=(--minor-prs "$minor")
  python3 "$CL" "${argv[@]}"
  git add -A .changes CHANGELOG.md
  commit "$ago" "chore(release): ${version}"
  replay
}

# ---- the history -----------------------------------------------------------
merge_pr 27 1283 feat "Add aws_byte_cursor_split for zero-copy tokenising"
merge_pr 25 1284 fix  "Correct the byte-buf append bounds check"
merge_pr 24 1285 chore "Bump the CI container image"
release  23 1.0.2 ""

merge_pr 21 1286 feat "Add tcp_nodelay to aws_socket_options" \
  "aws_socket_options grew from 40 to 44 bytes. Source-compatible, but a native
consumer that embeds the struct must be rebuilt."
merge_pr 20 1287 fix  "Retry backoff off-by-one"
release  19 1.1.0 "1286"

merge_pr 16 1288 fix  "Handle EINTR in the pipe read loop"
release  15 1.1.1 ""

merge_pr 12 1289 feat "Replace the event-loop dispatch queue" \
  "The old aws_event_loop_vtable layout is gone. Implementers of a custom event
loop must adopt the new vtable."
merge_pr 11 1290 feat "Add aws_uuid_to_compact_str"
merge_pr 10 1291 revert "Reverted the retry-default change" \
  "It changed behaviour customers relied on. A replacement lands in 1.3."
release   9 1.2.0 "1289"

merge_pr  6 1292 fix  "Leaking fd on socket teardown"
merge_pr  5 1293 chore "Bump aws-lc to 1.34"
release   4 1.2.1 ""

merge_pr  2 1294 feat "Add aws_uuid_v7 for time-ordered identifiers"
merge_pr  1 1295 fix  "Guard aws_hash_table against a zero-length key"

echo
echo "sim branch  ${SIM}:  $(git rev-list --count "${BASE}..${SIM}") commits on ${BASE}"
echo "docs branch ${DOCS}: $(git rev-list --count "${BASE}..${DOCS}") commits"
echo "no tag, no release, no artifact created"
