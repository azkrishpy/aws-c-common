"""Cutting a release."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402
from helpers import _changes, _rollup, _seed, _write  # noqa: E402


def _changelog(tmp_path):
    return (tmp_path / "CHANGELOG.md").read_text()


def test_a_release_renders_its_section_and_drops_the_fragments(tmp_path):
    _seed(tmp_path, 1, "feat: Add a widget")
    _seed(tmp_path, 2, "chore: Bump the CI image")
    assert _rollup(tmp_path, "1.0.2", "2026-09-06") == 0
    text = _changelog(tmp_path)
    assert "## [1.0.2] — 2026-09-06" in text
    assert "Add a widget." in text
    # The fragment is the input, not the record: it is gone once rendered.
    assert list((tmp_path / ".changes" / "preview").glob("*.json")) == []


def test_the_newest_release_sits_above_the_older_ones(tmp_path):
    _seed(tmp_path, 1, "feat: First")
    _rollup(tmp_path, "1.0.2", "2026-09-06")
    _seed(tmp_path, 2, "feat: Second")
    _rollup(tmp_path, "1.1.0", "2026-09-10")
    text = _changelog(tmp_path)
    assert text.index("## [1.1.0]") < text.index("## [1.0.2]")
    # A blank line between them, or the sections run together when rendered.
    assert "\n\n## [1.0.2]" in text


def test_a_released_section_is_never_rewritten(tmp_path):
    _seed(tmp_path, 1, "feat: First")
    _rollup(tmp_path, "1.0.2", "2026-09-06")
    before = _changelog(tmp_path).split("## [1.0.2]", 1)[1]
    _seed(tmp_path, 2, "feat: Second")
    _rollup(tmp_path, "1.1.0", "2026-09-10")
    assert _changelog(tmp_path).split("## [1.0.2]", 1)[1] == before


def test_re_running_a_release_changes_nothing(tmp_path):
    # The release job can fail after this step -- on the tag, or on the GitHub
    # release -- and be retried. The retry must not add a second section.
    _seed(tmp_path, 1, "feat: Add a widget")
    _rollup(tmp_path, "1.0.2", "2026-09-06")
    before = _changelog(tmp_path)
    assert _rollup(tmp_path, "1.0.2", "2026-09-06") == 0
    assert _changelog(tmp_path) == before


def test_a_release_with_nothing_visible_renders_no_section(tmp_path):
    # A bare header with nothing under it reads as a broken file.
    _seed(tmp_path, 1, "chore: Internal only")
    assert _rollup(tmp_path, "1.0.2", "2026-09-06") == 0
    assert "## [1.0.2]" not in _changelog(tmp_path)
    assert list((tmp_path / ".changes" / "preview").glob("*.json")) == []


def test_a_release_with_no_fragments_at_all_still_succeeds(tmp_path):
    # Failing here would fail the release job after it has already tagged.
    _changes(tmp_path)
    assert _rollup(tmp_path, "1.0.2", "2026-09-06") == 0


def test_the_release_branch_shows_the_pointer_not_the_unreleased_list(tmp_path):
    _seed(tmp_path, 1, "feat: Add a widget")
    _rollup(tmp_path, "1.0.2", "2026-09-06")
    text = _changelog(tmp_path)
    assert "## [Unreleased]" not in text
    assert "tree/docs/CHANGELOG.md" in text


def test_the_docs_branch_name_is_the_consumers_choice(tmp_path):
    _seed(tmp_path, 1, "feat: Add a widget")
    _rollup(tmp_path, "1.0.2", "2026-09-06", docs_branch="changelog-docs")
    assert "tree/changelog-docs/CHANGELOG.md" in _changelog(tmp_path)


def test_the_abi_label_decides_the_breaking_section(tmp_path):
    _seed(tmp_path, 20, "feat: Replace the socket options layout")
    _seed(tmp_path, 21, "feat: Add a knob")
    assert _rollup(tmp_path, "1.1.0", "2026-09-10", minor_prs="20") == 0
    text = _changelog(tmp_path)
    breaking = text.split("### Possible Breaking Changes", 1)[1].split("###", 1)[0]
    assert "#20" in breaking and "#21" not in breaking


def test_an_invalid_fragment_stops_the_release(tmp_path):
    # Releasing would delete it unrendered, so the entry would be lost rather
    # than merely late.
    _seed(tmp_path, 1, "feat: Good")
    (tmp_path / ".changes" / "preview" / "2.json").write_text("{ not json")
    assert _rollup(tmp_path, "1.0.2", "2026-09-06") == 2
    assert not (tmp_path / "CHANGELOG.md").exists()
    assert len(list((tmp_path / ".changes" / "preview").glob("*.json"))) == 2


def test_a_malformed_date_stops_the_release(tmp_path):
    _seed(tmp_path, 1, "feat: Good")
    assert _rollup(tmp_path, "1.0.2", "06-09-2026") == 2


def test_a_release_preserves_hand_written_content(tmp_path):
    # Adoption: whatever is in the file before the first release stays there.
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [1.0.0]\n\nOfficial release of 1.0.0.\n")
    _seed(tmp_path, 1, "feat: Add a widget")
    _rollup(tmp_path, "1.0.2", "2026-09-06")
    text = _changelog(tmp_path)
    assert "Official release of 1.0.0." in text
    assert text.index("## [1.0.2]") < text.index("## [1.0.0]")
