# Changelog fragments

Individual changes are recorded here as JSON fragments — one per PR. The
top-level [`CHANGELOG.md`](../CHANGELOG.md) is derived from these.

## Directory layout

```
.changes/
├── preview/                   # in-flight fragments, one JSON per PR
├── latest/                    # active minor line
│   └── <version>/  { *.json } # per-patch fragment dir (e.g. 0.30.0/, 0.30.1/)
├── <M>.<N>.x/                 # frozen prior minor line
│   └── CHANGELOG.md           # frozen snapshot: the whole archive for that line
└── …
```

A line frozen before this rule took effect still carries its fragments. Confirm
its snapshot is complete, then drop them once:

```sh
python3 -c "import sys;sys.path.insert(0,'.github/scripts');import changelog as c;\
  assert c.render_frozen_line('.changes/0.15.x') == open('.changes/0.15.x/CHANGELOG.md').read()"
git rm -r .changes/0.15.x/0.15.*
```

Freezing a minor line deletes its fragments and keeps only the snapshot.
Nothing reads a frozen fragment — every release guard works off directory names,
and a snapshot is never regenerated. Keeping them would add one checked-out file
per merged PR forever; `git log -- .changes` still has every one.

## Fragment schema

Each fragment is `.changes/preview/<PR-number>.json` while in flight, then
moves into `latest/<version>/` at release time.

```json
{
  "pr": 1212,
  "type": "feat",
  "summary": "Add an API for compact (dash-free) UUID-to-string conversion.",
  "url": "https://github.com/awslabs/aws-c-common/pull/1212",
  "notes": ""
}
```

| Field | Values |
|---|---|
| `pr` | PR number; also the filename |
| `type` | `feat` \| `fix` \| `doc` \| `chore` \| `revert` |
| `summary` | customer-facing one sentence |
| `url` | link to the PR |
| `notes` | optional extended notes |

## Finding a change

| You want | Look here |
|---|---|
| currently in-flight | `preview/*.json` on `main`, or the rendered view on the `docs` branch |
| in the current minor line (`X.Y.*`) | root [`CHANGELOG.md`](../CHANGELOG.md) |
| in a prior minor line (`A.B.*`) | `.changes/A.B.x/CHANGELOG.md` |
| the fragment behind an archived entry | `git log -- .changes` |
| exact set for a tag | GitHub Release page for that tag |

> Note: filesystem lex sort places `0.10.x/` before `0.2.x/`. The rendered `CHANGELOG.md` files are semver-sorted, so only raw `ls .changes/` looks out of order.
