import pytest

from slopo.config import load_config, ConfigError
from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures"


def test_load_config_reads_valid_file():
    cfg = load_config(FIXTURES / "config.yaml")
    assert cfg.embedding_model == "voyage/voyage-4-large"
    assert cfg.embedding_dimensions == 1024
    assert cfg.embedding_api_key == "test-key-12345"


def test_load_config_recognizes_embedding_param_types_from_yaml():
    cfg = load_config(FIXTURES / "config.yaml")

    params = cfg.embedding_params
    assert params["encoding_format"] == "float"
    assert params["output_dimension"] == 512
    assert isinstance(params["output_dimension"], int)
    assert params["temperature"] == 0.5
    assert isinstance(params["temperature"], float)
    assert params["truncation"] is False


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
