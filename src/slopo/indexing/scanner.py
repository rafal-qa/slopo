import logging
from pathlib import Path
from typing import Iterator

from pathspec import PathSpec

from slopo.indexing.parsing.base import CodeUnit
from slopo.indexing.parsing.registry import get_parser, supported_extensions

logger = logging.getLogger(__name__)

_MAX_BODY_CHARS = 10_000


def scan_directory(root: Path, exclude: list[str]) -> Iterator[str]:
    extensions = supported_extensions()
    spec = PathSpec.from_lines("gitignore", exclude)
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            relative = path.relative_to(root)
            if not spec.match_file(relative):
                # Normalize to forward slashes so relative paths have consistent format
                # in generated reports and cluster hashes used in the ignore file.
                yield relative.as_posix()


def parse_file(path: Path) -> list[CodeUnit]:
    parser = get_parser(path)
    try:
        source = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        return parser(source)
    except Exception as e:
        logger.warning("Skipping %s: %s", path, e)
        return []


def filter_units(
    units: list[CodeUnit], body_node_count_threshold: int
) -> list[CodeUnit]:
    return [
        u
        for u in units
        if u.body_node_count >= body_node_count_threshold
        and len(u.body) <= _MAX_BODY_CHARS
    ]
