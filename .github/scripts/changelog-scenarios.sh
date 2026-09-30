#!/usr/bin/env bash
# Behavioural scenarios for changelog.py, asserted on both exit code and the
# machine-readable reason the caller branches on. Exits non-zero on any
# mismatch. Called by changelog-selftest.yml and by its mutation check, so a
# mutation that changes a reason string is caught here rather than slipping past
# a suite that only looks at exit codes.
#
#   CL   path to changelog.py (required)
set -uo pipefail

: "${CL:?CL is required}"

WORK="$(mktemp -d)"
mkdir -p "${WORK}/.changes/preview"
pass=0
fail=0

frag() {
  printf '{"pr":%s,"type":"%s","summary":"%s","notes":"%s"}\n' \
    "$1" "$2" "$3" "${4:-}" > "${WORK}/.changes/preview/$1.json"
}

# expect <rc> <reason> <pr> <title> [extra args...]
expect() {
  local want_rc="$1" want_reason="$2" pr="$3" title="$4"; shift 4
  local out rc reason
  out="$(python3 "${CL}" check --pr "$pr" --title "$title" \
           --changes-dir "${WORK}/.changes" "$@" 2>&1)"; rc=$?
  reason="$(sed -n 's/^CHANGELOG_CHECK_REASON:://p' <<< "$out")"
  if [[ "$rc" == "$want_rc" && "$reason" == "$want_reason" ]]; then
    echo "ok    rc=$rc reason=$reason  <- ${LABEL:-$title}"; pass=$((pass+1))
  else
    echo "FAIL  want rc=$want_rc reason=$want_reason, got rc=$rc reason=$reason  <- ${LABEL:-$title}"
    fail=$((fail+1))
  fi
}

# paths <rc> <reason> <pr> <title> <label> <status:path>...
paths() {
  local want_rc="$1" want_reason="$2" pr="$3" title="$4" label="$5"; shift 5
  local pf="${WORK}/paths.$$.$RANDOM" e
  : > "$pf"
  for e in "$@"; do printf '%s\t%s\n' "${e%%:*}" "${e#*:}" >> "$pf"; done
  LABEL="$label" expect "$want_rc" "$want_reason" "$pr" "$title" \
    --changed-paths-file "$pf" --changes-prefix .changes
}

# ---------- the check gate ----------

expect 0 exempt-type      1 "chore: bump a pin"
expect 1 missing-fragment 2 "feat: add a thing"
expect 1 bad-title        3 "add a thing"
frag 4 revert "Reverted the retry default" "It changed behaviour customers relied on."
expect 0 ok               4 'Revert "fix: retry default (#3)"'
frag 5 feat "Add SSO sign-in"
expect 0 ok               5 "feat: add SSO sign-in"
frag 6 fix "Mislabelled"
expect 1 type-mismatch    6 "feat: add a thing"
printf '{"pr":7,"type":"feat","summary":"Wrong number","notes":""}\n' \
  > "${WORK}/.changes/preview/8.json"
expect 1 pr-mismatch      8 "feat: add a thing"
expect 0 waived-bot       9 "whatever" --bot-author "dependabot[bot]"
# A fragment at the right path that fails the schema.
printf '{"pr":11,"type":"feat","summary":"s","notes":7}\n' \
  > "${WORK}/.changes/preview/11.json"
expect 1 invalid-fragment 11 "feat: a thing"
# Documentation is a chore; `doc` is not a type.
expect 1 bad-title       10 "doc: something"
expect 1 bad-title       10 "docs: something"
expect 0 exempt-type     10 "chore: document the mutex"

# ---------- .changes/ integrity ----------

frag 30 feat "Mine"
frag 31 feat "Theirs"
paths 0 ok                30 "feat: mine"  "adds exactly its own fragment" \
  "added:.changes/preview/30.json"
paths 1 stray-fragment    30 "feat: mine"  "also adds someone else's" \
  "added:.changes/preview/30.json" "added:.changes/preview/9999.json"
paths 1 modified-fragment 30 "feat: mine"  "rewrites an existing fragment" \
  "modified:.changes/preview/30.json"
# A chore is a maintenance change: it may curate any preview fragment.
paths 0 exempt-type       32 "chore: tidy past entries" "chore curates another entry" \
  "modified:.changes/preview/31.json"

echo
echo "scenarios: ${pass} passed, ${fail} failed"
[[ "$fail" -eq 0 ]] || exit 1
exit 0
