from pathlib import Path


_HEADER = """\
# Cluster hashes reviewed and dismissed. One hash per line.
#
# A hash covers each unit's code body and its path relative to the index root.
# It changes when the code or that path changes, so the cluster re-surfaces.
# Re-indexing from a different root shifts every path, changing the hashes.

"""


def load_ignored(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    hashes: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.split("#", 1)[0].strip()
        if stripped:
            hashes.add(stripped)
    return hashes


def ensure_ignore_file(path: Path) -> None:
    if path.exists():
        return
    path.write_text(_HEADER, encoding="utf-8")
