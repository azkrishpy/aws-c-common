"""Cutting a release: render the fragments awaiting one, then drop them.

No version guard. The version comes from the release job, and a mistake in the
rendered file is fixed by a chore -- the file is markdown, not a database.
"""
import re
from pathlib import Path

from fragments import _err, load_preview
from render import insert_release, render_release_section, set_region, \
    unreleased_pointer

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def cmd_rollup(args):
    """Insert this release's section, then delete the fragments it rendered.

    Re-running it is a no-op: the fragments are gone, so there is nothing left to
    insert. That matters because a release job that fails after this step -- on
    the tag, or on the GitHub release -- is retried.
    """
    if not ISO_DATE_RE.match(args.date):
        _err(f"--date must be YYYY-MM-DD, got {args.date!r}")
        return 2

    changes = Path(args.changes_dir)
    on_disk = sorted((changes / "preview").glob("*.json"))
    fragments = load_preview(changes)
    if len(fragments) != len(on_disk):
        # Releasing anyway would delete the rejected fragments unrendered, so the
        # entry would be lost rather than merely late.
        _err(f"{len(on_disk) - len(fragments)} of {len(on_disk)} fragment(s) in "
             f"{changes / 'preview'} are invalid (see the warnings above); "
             f"fix them first")
        return 2

    minor_prs = {int(p) for p in args.minor_prs.split(",") if p.strip()}
    section = render_release_section(args.version, args.date, fragments, minor_prs)

    path = Path(args.changelog)
    text = path.read_text() if path.exists() else ""
    # The release branch's region is the pointer, not the unreleased list: only a
    # release rewrites this file, so a list of unreleased changes would sit stale.
    text = set_region(text, unreleased_pointer(args.docs_branch))
    path.write_text(insert_release(text, section))

    for f in on_disk:
        f.unlink()
    print(f"released {len(fragments)} fragment(s) as {args.version}"
          + ("" if section else " (nothing customer-facing, so no section)"))
    return 0
