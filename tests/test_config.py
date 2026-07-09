from pathlib import Path

import pytest

from slopo.config import ConfigError, load_config, mask_api_key, parse_config


@pytest.fixture(autouse=True)
def _clear_api_key_env(monkeypatch):
    monkeypatch.delenv("SLOPO_EMBEDDING_API_KEY", raising=False)


def _minimal_raw(**overrides):
    raw = {
        "source_dir": "/tmp/my-project",
        "embedding_model": "voyage/voyage-code-3",
        "embedding_dimensions": 1024,
        "embedding_api_key": "test-key-12345",
    }
    raw.update(overrides)
    return raw


# --- happy paths ---


def test_returns_config_with_defaults_when_only_required_fields_present():
    cfg = parse_config(_minimal_raw(), source="<test>")

    assert cfg.source_dir == Path("/tmp/my-project")
    assert cfg.db_file == Path("slopo.db")
    assert cfg.report_dir == Path("slopo-report")
    assert cfg.ignore_file == Path("slopo.ignore.txt")
    assert cfg.embedding_model == "voyage/voyage-code-3"
    assert cfg.embedding_dimensions == 1024
    assert cfg.embedding_api_key == "test-key-12345"
    assert cfg.embedding_api_base is None
    assert cfg.embedding_batch_size == 100
    assert cfg.embedding_batch_chars == 100_000
    assert cfg.similarity_threshold == 0.92
    assert cfg.rerank_threshold == 0.94
    assert cfg.body_node_count_threshold == 10


def test_overrides_defaults_when_optional_fields_present():
    cfg = parse_config(
        _minimal_raw(
            embedding_batch_size=50,
            similarity_threshold=0.85,
            rerank_threshold=0.95,
        ),
        source="<test>",
    )

    assert cfg.embedding_batch_size == 50
    assert cfg.similarity_threshold == 0.85
    assert cfg.rerank_threshold == 0.95


# --- field validation ---


def test_missing_required_field_reports_key_name():
    raw = _minimal_raw()
    del raw["embedding_model"]
    with pytest.raises(ConfigError, match="'embedding_model' is required"):
        parse_config(raw, source="<test>")


def test_empty_string_for_required_field_treated_as_missing():
    with pytest.raises(ConfigError, match="'embedding_model' is required"):
        parse_config(_minimal_raw(embedding_model=""), source="<test>")


def test_wrong_type_reports_key_and_value():
    with pytest.raises(
        ConfigError, match="'embedding_dimensions' must be an integer, got 'abc'"
    ):
        parse_config(_minimal_raw(embedding_dimensions="abc"), source="<test>")


def test_negative_value_rejected_as_not_positive():
    with pytest.raises(
        ConfigError, match="'embedding_dimensions' must be positive, got -1"
    ):
        parse_config(_minimal_raw(embedding_dimensions=-1), source="<test>")


def test_negative_optional_int_rejected():
    with pytest.raises(
        ConfigError, match="'embedding_batch_size' must be positive, got -5"
    ):
        parse_config(_minimal_raw(embedding_batch_size=-5), source="<test>")


def test_wrong_type_optional_float_rejected():
    with pytest.raises(
        ConfigError, match="'similarity_threshold' must be a number, got '0.9'"
    ):
        parse_config(_minimal_raw(similarity_threshold="0.9"), source="<test>")


# --- source_dir ---


def test_source_dir_parsed_as_path():
    cfg = parse_config(_minimal_raw(source_dir="/tmp/other"), source="<test>")
    assert cfg.source_dir == Path("/tmp/other")


def test_missing_source_dir_rejected():
    raw = _minimal_raw()
    del raw["source_dir"]
    with pytest.raises(ConfigError, match="'source_dir' is required"):
        parse_config(raw, source="<test>")


def test_source_dir_empty_string_rejected():
    with pytest.raises(ConfigError, match="'source_dir' is required"):
        parse_config(_minimal_raw(source_dir=""), source="<test>")


def test_source_dir_wrong_type_rejected():
    with pytest.raises(ConfigError, match="'source_dir' must be a string"):
        parse_config(_minimal_raw(source_dir=123), source="<test>")


# --- source_dir_exclude ---


def test_source_dir_exclude_defaults_to_empty_list_when_absent():
    cfg = parse_config(_minimal_raw(), source="<test>")
    assert cfg.source_dir_exclude == []


def test_source_dir_exclude_parsed_as_list_of_patterns():
    cfg = parse_config(
        _minimal_raw(source_dir_exclude=["build/", "*.gen.kt"]), source="<test>"
    )
    assert cfg.source_dir_exclude == ["build/", "*.gen.kt"]


def test_source_dir_exclude_non_list_rejected():
    with pytest.raises(ConfigError, match="'source_dir_exclude' must be a list"):
        parse_config(_minimal_raw(source_dir_exclude="build/"), source="<test>")


def test_source_dir_exclude_non_string_item_rejected():
    with pytest.raises(
        ConfigError, match="'source_dir_exclude' items must be non-empty strings"
    ):
        parse_config(_minimal_raw(source_dir_exclude=["build/", 123]), source="<test>")


def test_source_dir_exclude_empty_string_item_rejected():
    with pytest.raises(
        ConfigError, match="'source_dir_exclude' items must be non-empty strings"
    ):
        parse_config(_minimal_raw(source_dir_exclude=[""]), source="<test>")


# --- path overrides ---


def test_path_fields_parsed_from_config():
    cfg = parse_config(
        _minimal_raw(
            db_file="custom.db",
            report_dir="reports",
            ignore_file="skip.txt",
        ),
        source="<test>",
    )
    assert cfg.db_file == Path("custom.db")
    assert cfg.report_dir == Path("reports")
    assert cfg.ignore_file == Path("skip.txt")


# --- API key ---


def test_api_key_read_from_config_file():
    cfg = parse_config(_minimal_raw(embedding_api_key="from-file"), source="<test>")
    assert cfg.embedding_api_key == "from-file"


def test_env_var_overrides_config_file_api_key(monkeypatch):
    monkeypatch.setenv("SLOPO_EMBEDDING_API_KEY", "from-env")
    cfg = parse_config(_minimal_raw(embedding_api_key="from-file"), source="<test>")
    assert cfg.embedding_api_key == "from-env"


def test_missing_api_key_in_both_sources_defaults_to_none():
    raw = _minimal_raw()
    del raw["embedding_api_key"]
    cfg = parse_config(raw, source="<test>")
    assert cfg.embedding_api_key is None


# --- API base ---


def test_api_base_read_from_config_file():
    cfg = parse_config(
        _minimal_raw(embedding_api_base="http://localhost:1234"), source="<test>"
    )
    assert cfg.embedding_api_base == "http://localhost:1234"


def test_missing_api_base_defaults_to_none():
    cfg = parse_config(_minimal_raw(), source="<test>")
    assert cfg.embedding_api_base is None


def test_api_base_wrong_type_rejected():
    with pytest.raises(ConfigError, match="'embedding_api_base' must be a string"):
        parse_config(_minimal_raw(embedding_api_base=123), source="<test>")


# --- mask_api_key ---


def test_mask_short_key_fully_hidden():
    assert mask_api_key("a" * 11) == "*****"


def test_mask_long_key_keeps_first_and_last_five_chars():
    key = "voyage-1234567890abcdef"
    assert mask_api_key(key) == "voyag...bcdef"


# --- load_config: file I/O wrapper ---


def test_load_config_reads_valid_file(tmp_path):
    path = tmp_path / "slopo.conf.yaml"
    path.write_text(
        "source_dir: /tmp/my-project\n"
        "embedding_model: voyage/voyage-code-3\n"
        "embedding_dimensions: 1024\n"
        "embedding_api_key: test-key-12345\n"
    )
    cfg = load_config(path)
    assert cfg.embedding_model == "voyage/voyage-code-3"
    assert cfg.embedding_dimensions == 1024
    assert cfg.embedding_api_key == "test-key-12345"


def test_load_config_handles_empty_file(tmp_path):
    path = tmp_path / "slopo.conf.yaml"
    path.write_text("")
    with pytest.raises(ConfigError, match="'source_dir' is required"):
        load_config(path)


def test_load_config_detects_missing_space_after_colon(tmp_path):
    path = tmp_path / "slopo.conf.yaml"
    path.write_text(
        "embedding_model: m\nembedding_dimensions:1024\nembedding_api_key: k\n"
    )
    with pytest.raises(ConfigError) as exc:
        load_config(path)
    msg = str(exc.value)
    assert ":2:" in msg
    assert "missing space after ':'" in msg
