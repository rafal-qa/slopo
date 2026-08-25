from pathlib import Path

from slopo.result.analysis.ignore import (
    ensure_ignore_file,
    load_ignored,
)
from slopo.result.models import UnitRecord


def unit(unit_id: int, file_path: str, body_hash: str) -> UnitRecord:
    return UnitRecord(
        unit_id=unit_id,
        file_path=file_path,
        name="",
        start_line=1,
        end_line=10,
        body="",
        body_hash=body_hash,
    )


# --- load_ignored ---


def test_missing_file_yields_an_empty_set(tmp_path: Path):
    assert load_ignored(tmp_path / "absent.txt") == set()


def test_reads_hashes_skipping_blank_and_comment_lines(tmp_path: Path):
    path = tmp_path / "ignore.txt"
    path.write_text("# header\n\nabc123\n\n# note\ndef456\n", encoding="utf-8")
    assert load_ignored(path) == {"abc123", "def456"}


def test_strips_inline_comments_and_surrounding_whitespace(tmp_path: Path):
    path = tmp_path / "ignore.txt"
    path.write_text("  abc123  # reviewed\n", encoding="utf-8")
    assert load_ignored(path) == {"abc123"}


# --- ensure_ignore_file ---


def test_writes_header_when_absent(tmp_path: Path):
    path = tmp_path / "ignore.txt"
    ensure_ignore_file(path)
    content = path.read_text(encoding="utf-8")
    assert content.startswith("#")


def test_leaves_an_existing_file_untouched(tmp_path: Path):
    path = tmp_path / "ignore.txt"
    path.write_text("my-hash\n", encoding="utf-8")
    ensure_ignore_file(path)
    assert path.read_text(encoding="utf-8") == "my-hash\n"
