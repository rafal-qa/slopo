from slopo.result.review.git.diff import parse_diff, parse_untracked
from slopo.result.review.models import LineRange, GitChange


# --- parse_diff ---


def test_extracts_path_and_line_range_from_modified_file():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "index abc..def 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -10,3 +10,5 @@\n"
        "+added\n"
    )

    result = parse_diff(diff)

    assert result == [
        GitChange(path_git="foo.py", is_new=False, changed_ranges=[LineRange(10, 14)])
    ]


def test_collects_multiple_hunks_for_one_file():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "index abc..def 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -5,0 +6,2 @@\n"
        "+a\n"
        "+b\n"
        "@@ -20,2 +22,3 @@\n"
        "+c\n"
    )

    result = parse_diff(diff)

    assert result == [
        GitChange(
            path_git="foo.py",
            is_new=False,
            changed_ranges=[LineRange(6, 7), LineRange(22, 24)],
        )
    ]


def test_handles_multiple_files():
    diff = (
        "diff --git a/a.py b/a.py\n"
        "--- a/a.py\n"
        "+++ b/a.py\n"
        "@@ -1,0 +2,1 @@\n"
        "+x\n"
        "diff --git a/b.py b/b.py\n"
        "--- a/b.py\n"
        "+++ b/b.py\n"
        "@@ -5,0 +6,3 @@\n"
        "+y\n"
    )

    result = parse_diff(diff)

    assert result == [
        GitChange(path_git="a.py", is_new=False, changed_ranges=[LineRange(2, 2)]),
        GitChange(path_git="b.py", is_new=False, changed_ranges=[LineRange(6, 8)]),
    ]


def test_marks_new_file_as_is_new():
    diff = (
        "diff --git a/new.py b/new.py\n"
        "new file mode 100644\n"
        "index 0000000..abc1234\n"
        "--- /dev/null\n"
        "+++ b/new.py\n"
        "@@ -0,0 +1,3 @@\n"
        "+line1\n"
    )

    result = parse_diff(diff)

    assert result == [
        GitChange(path_git="new.py", is_new=True, changed_ranges=[LineRange(1, 3)])
    ]


def test_excludes_deleted_file():
    diff = (
        "diff --git a/old.py b/old.py\n"
        "deleted file mode 100644\n"
        "index abc1234..0000000\n"
        "--- a/old.py\n"
        "+++ /dev/null\n"
        "@@ -1,5 +0,0 @@\n"
        "-removed\n"
    )

    result = parse_diff(diff)

    assert result == []


def test_treats_omitted_count_as_single_line():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -10,1 +10 @@\n"
        "+changed\n"
    )

    result = parse_diff(diff)

    assert result == [
        GitChange(path_git="foo.py", is_new=False, changed_ranges=[LineRange(10, 10)])
    ]


def test_records_deletion_point_as_single_line_range():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -5,3 +4,0 @@\n"
        "-removed\n"
    )

    result = parse_diff(diff)

    assert result == [
        GitChange(path_git="foo.py", is_new=False, changed_ranges=[LineRange(4, 4)])
    ]


def test_empty_diff_returns_no_files():
    assert parse_diff("") == []


# --- parse_untracked ---


def test_parses_untracked_file_paths():
    ls_output = "src/new.py\nlib/util.js\n"

    result = parse_untracked(ls_output)

    assert result == [
        GitChange(path_git="src/new.py", is_new=True, changed_ranges=[]),
        GitChange(path_git="lib/util.js", is_new=True, changed_ranges=[]),
    ]


def test_empty_untracked_output_returns_no_files():
    assert parse_untracked("") == []
