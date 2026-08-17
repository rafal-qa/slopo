import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


_CONFIG_TEMPLATE = """\
# Source directory with code to index.
# Absolute path, or relative to the current directory.
source_dir:

# Paths to exclude from indexing, as a YAML list of .gitignore-style patterns
#source_dir_exclude:
#  - "**/test/**"
#  - "*.test.ts"

# Embedding model in LiteLLM format, e.g. "jina_ai/jina-code-embeddings-0.5b"
# For all supported providers see https://docs.litellm.ai/docs/providers
embedding_model:

# Output dimensions of the embedding model.
embedding_dimensions:

# Provider API key. Optional, no need to set for local models.
# Alternatively, set the SLOPO_EMBEDDING_API_KEY environment variable
# (also picked up from a .env file in the current directory)
embedding_api_key:
"""


class ConfigError(Exception):
    pass


@dataclass
class Config:
    source_dir: Path
    source_dir_exclude: list[str]
    db_file: Path
    report_dir: Path
    ignore_file: Path
    embedding_model: str
    embedding_dimensions: int
    embedding_api_key: str | None
    embedding_params: dict[str, str | int | float | bool]
    embedding_batch_size: int
    embedding_batch_chars: int
    similarity_threshold: float
    rerank_threshold: float
    body_node_count_threshold: int


def load_config(path: Path) -> Config:
    if not path.is_file():
        raise ConfigError(
            f"no config file found at {path}. Run `slopo init` to create one."
        )

    text = path.read_text(encoding="utf-8")
    source = str(path)
    _check_missing_space_after_colon(text, source)

    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ConfigError(f"failed to parse {source}: {e}")

    return parse_config(raw, source)


_KNOWN_CONFIG_KEYS = {
    "source_dir",
    "source_dir_exclude",
    "db_file",
    "report_dir",
    "ignore_file",
    "embedding_model",
    "embedding_dimensions",
    "embedding_api_key",
    "embedding_params",
    "embedding_batch_size",
    "embedding_batch_chars",
    "similarity_threshold",
    "rerank_threshold",
    "body_node_count_threshold",
}


def parse_config(raw: Any, source: str) -> Config:
    if raw is None:
        raw = {}

    for key in raw:
        if key not in _KNOWN_CONFIG_KEYS:
            raise ConfigError(f"{source}: unrecognized config key '{key}'")

    return Config(
        source_dir=_require_path(raw, "source_dir", source),
        source_dir_exclude=_optional_str_list(raw, "source_dir_exclude", source),
        db_file=_optional_path(raw, "db_file", source, default=Path("slopo.db")),
        report_dir=_optional_path(
            raw, "report_dir", source, default=Path("slopo-report")
        ),
        ignore_file=_optional_path(
            raw, "ignore_file", source, default=Path("slopo.ignore.txt")
        ),
        embedding_model=_require_str(raw, "embedding_model", source),
        embedding_dimensions=_require_positive_int(raw, "embedding_dimensions", source),
        embedding_api_key=_optional_api_key(raw, source),
        embedding_params=_optional_params_map(raw, "embedding_params", source),
        embedding_batch_size=_optional_positive_int(
            raw, "embedding_batch_size", source, default=100
        ),
        embedding_batch_chars=_optional_positive_int(
            raw, "embedding_batch_chars", source, default=100_000
        ),
        similarity_threshold=_optional_positive_float(
            raw, "similarity_threshold", source, default=0.92
        ),
        rerank_threshold=_optional_positive_float(
            raw, "rerank_threshold", source, default=0.94
        ),
        body_node_count_threshold=_optional_positive_int(
            raw, "body_node_count_threshold", source, default=10
        ),
    )


def write_config_template(path: Path) -> None:
    if path.exists():
        raise ConfigError(f"{path} already exists")
    path.write_text(_CONFIG_TEMPLATE, encoding="utf-8")


def mask_api_key(key: str) -> str:
    if len(key) < 12:
        return "*****"
    return f"{key[:5]}...{key[-5:]}"


def _check_missing_space_after_colon(text: str, source: str) -> None:
    pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*:\S")
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if pattern.match(stripped):
            raise ConfigError(
                f"{source}:{lineno}: missing space after ':'."
                " Write 'key: value', not 'key:value'."
            )


def _optional_api_key(raw: dict[str, Any], source: str) -> str | None:
    from_env = os.environ.get("SLOPO_EMBEDDING_API_KEY")
    return from_env or _optional_str(raw, "embedding_api_key", source)


def _require_str(raw: dict[str, Any], key: str, source: str) -> str:
    value = raw.get(key)
    if value is None or value == "":
        raise ConfigError(f"{source}: '{key}' is required")
    if not isinstance(value, str):
        raise ConfigError(f"{source}: '{key}' must be a string")
    return value


def _optional_str(raw: dict[str, Any], key: str, source: str) -> str | None:
    value = raw.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ConfigError(f"{source}: '{key}' must be a string")
    return value


def _optional_str_list(raw: dict[str, Any], key: str, source: str) -> list[str]:
    value = raw.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError(f"{source}: '{key}' must be a list")
    items = []
    for item in value:
        if not isinstance(item, str) or item == "":
            raise ConfigError(
                f"{source}: '{key}' items must be non-empty strings, got {item!r}"
            )
        items.append(item)
    return items


_RESERVED_EMBEDDING_PARAMS = ("model", "input", "dimensions", "api_key")


def _optional_params_map(
    raw: dict[str, Any], key: str, source: str
) -> dict[str, str | int | float | bool]:
    value = raw.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{source}: '{key}' must be a mapping of keys and values")
    params: dict[str, str | int | float | bool] = {}
    for name, item in value.items():
        if not isinstance(name, str) or name == "":
            raise ConfigError(
                f"{source}: '{key}' keys must be non-empty strings, got {name!r}"
            )
        if name in _RESERVED_EMBEDDING_PARAMS:
            raise ConfigError(f"{source}: '{key}' cannot set '{name}'")
        if not isinstance(item, (str, int, float, bool)):
            raise ConfigError(
                f"{source}: '{key}.{name}' must be a string, number, or boolean,"
                f" got {item!r}"
            )
        params[name] = item
    return params


def _require_path(raw: dict[str, Any], key: str, source: str) -> Path:
    return Path(_require_str(raw, key, source))


def _optional_path(raw: dict[str, Any], key: str, source: str, default: Path) -> Path:
    value = _optional_str(raw, key, source)
    return Path(value) if value is not None else default


def _require_positive_int(raw: dict[str, Any], key: str, source: str) -> int:
    value = raw.get(key)
    if value is None:
        raise ConfigError(f"{source}: '{key}' is required")
    return _ensure_positive_int(value, key, source)


def _optional_positive_int(
    raw: dict[str, Any], key: str, source: str, default: int
) -> int:
    value = raw.get(key)
    if value is None:
        return default
    return _ensure_positive_int(value, key, source)


def _optional_positive_float(
    raw: dict[str, Any], key: str, source: str, default: float
) -> float:
    value = raw.get(key)
    if value is None:
        return default
    return _ensure_positive_float(value, key, source)


def _ensure_positive_int(value: Any, key: str, source: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{source}: '{key}' must be an integer, got {value!r}")
    if value <= 0:
        raise ConfigError(f"{source}: '{key}' must be positive, got {value}")
    return value


def _ensure_positive_float(value: Any, key: str, source: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{source}: '{key}' must be a number, got {value!r}")
    if value <= 0:
        raise ConfigError(f"{source}: '{key}' must be positive, got {value}")
    return float(value)
