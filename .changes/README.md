# Changelog fragments

Individual changes are recorded here as JSON fragments — one per PR. The
top-level [`CHANGELOG.md`](../CHANGELOG.md) is derived from these.

Nothing before 1.0.0 is in the changelog: those releases shipped without
fragments, so rolling one up would publish entries that do not exist.

## Directory layout

```
.changes/
├── preview/<PR>.json          # in-flight, written by the PR author
├── released/<PR>.json         # shipped; carries its version and date
├── <M>.<N>.x.md               # archive of a closed minor line
└── …
```

A fragment is the only state. `version` and `date` are stamped onto it at
release, so a release has no side file of its own — the releases in `released/`
are those fragments grouped by the version they carry.

Archiving a minor line deletes its fragments and keeps only `<M>.<N>.x.md`.
Nothing reads an archived fragment and the file is never regenerated. Keeping
them would add one checked-out file per merged PR forever; `git log -- .changes`
still has every one.

## Fragment schema

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
| `type` | `feat` \| `fix` \| `chore` \| `revert` |
| `summary` | customer-facing one sentence |
| `url` | link to the PR |
| `notes` | optional extended notes; rendered as their own entry |

`version`, `date` and `impact` are added at release time and rejected from a
PR's fragment — `impact` decides whether the entry renders under Possible
Breaking Changes, and the ABI check settles that, not the PR.

## Finding a change

| You want | Look here |
|---|---|
| currently in-flight | `preview/*.json` on `main`, or the rendered view on the `docs` branch |
| in the current minor line (`X.Y.*`) | root [`CHANGELOG.md`](../CHANGELOG.md) |
| in a closed minor line (`A.B.*`) | `.changes/A.B.x.md` |
| the fragment behind an archived entry | `git log -- .changes` |
| exact set for a tag | GitHub Release page for that tag |
