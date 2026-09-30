# Changelog fragments

A pull request records its change here as one JSON fragment. A release renders the fragments into the top-level [`CHANGELOG.md`](../CHANGELOG.md) and deletes them, so this directory only ever holds what has not shipped yet.

Nothing before 1.0.0 is in the changelog: those releases shipped without fragments, and nothing backfills them.

```
.changes/preview/<PR>.json     awaiting release, written by the PR author
.changes/<M>.<N>.x.md          a closed minor line, moved out of the root
```

The rendered file is the record — it is never regenerated, so a published entry cannot change under a reader. The root holds the minor version line currently being released into; when a new minor opens, the closed line's sections move to `.changes/<M>.<N>.x.md` and the root links it under Earlier releases.

## Fragment schema

```json
{
  "pr": 1212,
  "type": "feat",
  "summary": "Add an API for compact (dash-free) UUID-to-string conversion.",
  "notes": ""
}
```

| Field | Values |
|---|---|
| `pr` | PR number; also the filename, and what the entry's link is built from |
| `type` | `feat` \| `fix` \| `chore` \| `revert` |
| `summary` | customer-facing, one sentence |
| `notes` | optional extended notes; rendered as their own entry |

The schema is closed: any other field is an error, so a misspelling is caught rather than silently ignored. Whether a change is breaking is settled by the `minor` label on the PR — the ABI check proposes it, a maintainer can override it, and the release reads the label. It is never stored in a fragment.

A `chore` needs no fragment — it renders nowhere, so an entry would be invisible. A CI-only or pure-infra change is a `chore`.

## Finding a change

| You want | Look here |
|---|---|
| released in the current minor line | [`CHANGELOG.md`](../CHANGELOG.md), newest first |
| released in an earlier line | `.changes/<M>.<N>.x.md`, linked from the root |
| merged but unreleased | `preview/*.json`, or the rendered view on the `docs` branch |
| the fragment behind a released entry | `git log -- .changes` |
| the exact set for a tag | the GitHub Release page for that tag |
