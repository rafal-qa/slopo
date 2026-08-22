from pathlib import Path

from slopo.indexing.scanner import filter_units, parse_file, scan_directory

_JAVA = """\
class Calculator {
    int increment(int a) {
        return a + 1;
    }
}
"""

_KOTLIN = """\
fun increment(a: Int): Int {
    return a + 1
}
"""


def test_scans_all_supported_languages(tmp_path: Path):
    (tmp_path / "Calculator.java").write_text(_JAVA)
    (tmp_path / "Increment.kt").write_text(_KOTLIN)

    scanned = set(scan_directory(tmp_path, exclude=[]))

    assert scanned == {"Calculator.java", "Increment.kt"}


def test_parses_units_from_each_language(tmp_path: Path):
    (tmp_path / "Calculator.java").write_text(_JAVA)
    (tmp_path / "Increment.kt").write_text(_KOTLIN)

    java_units = parse_file(tmp_path / "Calculator.java")
    kotlin_units = parse_file(tmp_path / "Increment.kt")

    assert [u.name for u in java_units] == ["increment"]
    assert [u.name for u in kotlin_units] == ["increment"]


def test_recurses_into_subdirectories_with_paths_relative_to_root(tmp_path: Path):
    (tmp_path / "sub" / "nested").mkdir(parents=True)
    (tmp_path / "sub" / "nested" / "Increment.kt").write_text(_KOTLIN)

    scanned = list(scan_directory(tmp_path, exclude=[]))

    assert scanned == ["sub/nested/Increment.kt"]


def test_ignores_unsupported_file_types(tmp_path: Path):
    (tmp_path / "notes.txt").write_text("not code")
    (tmp_path / "data.json").write_text("{}")

    assert list(scan_directory(tmp_path, exclude=[])) == []


def test_excludes_units_below_body_node_count_threshold(tmp_path: Path):
    (tmp_path / "Calculator.java").write_text(_JAVA)
    units = parse_file(tmp_path / "Calculator.java")

    filtered = filter_units(units, body_node_count_threshold=1000)

    assert filtered == []


def test_excludes_units_exceeding_max_body_chars(tmp_path: Path):
    big_body = "\n".join(f"        int x{i} = {i};" for i in range(500))
    assert len(big_body) == 11779
    source = (
        "class Big {\n"
        "    void huge() {\n"
        f"{big_body}\n"
        "    }\n"
        "    int small(int a) {\n"
        "        return a + 1;\n"
        "    }\n"
        "}\n"
    )
    (tmp_path / "Big.java").write_text(source)
    units = parse_file(tmp_path / "Big.java")

    filtered = filter_units(units, body_node_count_threshold=0)

    assert [u.name for u in filtered] == ["small"]


def test_skips_files_under_excluded_directory(tmp_path: Path):
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "Generated.kt").write_text(_KOTLIN)
    (tmp_path / "Increment.kt").write_text(_KOTLIN)

    scanned = list(scan_directory(tmp_path, exclude=["build/"]))

    assert scanned == ["Increment.kt"]


def test_skips_files_matching_glob_pattern(tmp_path: Path):
    (tmp_path / "Increment.gen.kt").write_text(_KOTLIN)
    (tmp_path / "Increment.kt").write_text(_KOTLIN)

    scanned = list(scan_directory(tmp_path, exclude=["*.gen.kt"]))

    assert scanned == ["Increment.kt"]


def test_negation_pattern_reincludes_excluded_file(tmp_path: Path):
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "Keep.kt").write_text(_KOTLIN)
    (tmp_path / "build" / "Drop.kt").write_text(_KOTLIN)

    scanned = list(scan_directory(tmp_path, exclude=["build/", "!build/Keep.kt"]))

    assert scanned == ["build/Keep.kt"]
