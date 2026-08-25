import subprocess
from pathlib import Path


class GitError(Exception):
    pass


# Path in posix format on Windows -> no need for normalization
def git_show_prefix(cwd: Path) -> str:
    return _run(["git", "rev-parse", "--show-prefix"], cwd=cwd)


def git_diff(base_ref: str, cwd: Path) -> str:
    return _run(["git", "diff", base_ref, "-U0"], cwd=cwd)


def git_version() -> str:
    return _run(["git", "--version"])


def git_ls_untracked(cwd: Path) -> str:
    return _run(
        ["git", "ls-files", "--full-name", "--others", "--exclude-standard"], cwd=cwd
    )


def _run(args: list[str], cwd: Path | None = None) -> str:
    try:
        r = subprocess.run(
            args,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
        )
    except FileNotFoundError as e:
        raise GitError(str(e))
    if r.returncode != 0:
        raise GitError(r.stderr.strip())
    return r.stdout.strip()
