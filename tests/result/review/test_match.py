from slopo.result.review.match import match_changed_units, to_changed_file
from slopo.result.review.models import ChangedFile, GitChange, LineRange, UnitRange

_RANGES = [LineRange(1, 5)]


# --- to_changed_file ---


def test_preserves_paths_when_source_dir_is_repo_root():
    changes = [
        GitChange(path_git="src/Foo.java", is_new=True, changed_ranges=_RANGES),
        GitChange(path_git="lib/Bar.java", is_new=False, changed_ranges=_RANGES),
    ]

    result = to_changed_file(changes, source_dir_prefix="")

    assert result == [
        ChangedFile(path_db="src/Foo.java", is_new=True, changed_ranges=_RANGES),
        ChangedFile(path_db="lib/Bar.java", is_new=False, changed_ranges=_RANGES),
    ]


def test_converts_git_paths_to_source_dir_relative():
    changes = [
        GitChange(path_git="repo/src/Foo.java", is_new=False, changed_ranges=_RANGES),
    ]

    result = to_changed_file(changes, source_dir_prefix="repo/")

    assert result == [
        ChangedFile(path_db="src/Foo.java", is_new=False, changed_ranges=_RANGES),
    ]


def test_ignores_paths_outside_source_directory():
    changes = [
        GitChange(path_git="repo/src/Foo.java", is_new=False, changed_ranges=_RANGES),
        GitChange(path_git="other/Bar.java", is_new=False, changed_ranges=_RANGES),
    ]

    result = to_changed_file(changes, source_dir_prefix="repo/")

    assert result == [
        ChangedFile(path_db="src/Foo.java", is_new=False, changed_ranges=_RANGES),
    ]


# --- match_changed_units ---


def test_new_file_matches_all_units():
    changed_files = [
        ChangedFile(path_db="a.py", is_new=True, changed_ranges=[]),
    ]
    units_by_path = {
        "a.py": [
            UnitRange(id=1, start_line=1, end_line=5),
            UnitRange(id=2, start_line=10, end_line=20),
        ],
    }

    result = match_changed_units(changed_files, units_by_path)

    assert result == [1, 2]


def test_existing_file_matches_only_overlapping_units():
    changed_files = [
        ChangedFile(path_db="a.py", is_new=False, changed_ranges=[LineRange(5, 10)]),
    ]
    units_by_path = {
        "a.py": [
            UnitRange(id=1, start_line=1, end_line=4),
            UnitRange(id=2, start_line=8, end_line=15),
            UnitRange(id=3, start_line=20, end_line=30),
        ],
    }

    result = match_changed_units(changed_files, units_by_path)

    assert result == [2]


def test_skips_files_not_in_units_by_path():
    changed_files = [
        ChangedFile(path_db="x.py", is_new=False, changed_ranges=[LineRange(2, 5)]),
    ]
    units_by_path = {
        "a.py": [UnitRange(id=1, start_line=2, end_line=5)],
    }

    result = match_changed_units(changed_files, units_by_path)

    assert result == []


def test_combines_matched_units_across_files():
    changed_files = [
        ChangedFile(path_db="a.py", is_new=True, changed_ranges=[]),
        ChangedFile(path_db="b.py", is_new=False, changed_ranges=[LineRange(1, 5)]),
    ]
    units_by_path = {
        "a.py": [UnitRange(id=1, start_line=1, end_line=10)],
        "b.py": [UnitRange(id=2, start_line=3, end_line=8)],
    }

    result = match_changed_units(changed_files, units_by_path)

    assert result == [1, 2]
