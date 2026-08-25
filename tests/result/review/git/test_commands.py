import shutil
import subprocess
from pathlib import Path

import pytest

from slopo.result.review.git.commands import (
    GitError,
    _run,
    git_diff,
    git_ls_untracked,
    git_show_prefix,
    git_version,
)

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


@pytest.fixture
def git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig-absent"))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(tmp_path / "gitconfig-absent"))
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    return tmp_path


@pytest.fixture
def non_git_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(repo: Path, relpath: Path, content: str) -> None:
    p = repo / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _commit_all(repo: Path) -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "commit"], cwd=repo, check=True)


# --- git_version ---


def test_returns_git_version_string():
    assert git_version().startswith("git version")


# --- git_show_prefix ---


def test_show_prefix_is_empty_at_repo_root(git_repo: Path):
    assert git_show_prefix(git_repo) == ""


def test_show_prefix_returns_relative_path_from_subdir(git_repo: Path):
    subdir = git_repo / "sub" / "dir"
    subdir.mkdir(parents=True)
    assert git_show_prefix(subdir) == "sub/dir/"


def test_show_prefix_raises_outside_git_repo(non_git_dir: Path):
    with pytest.raises(GitError):
        git_show_prefix(non_git_dir)


# --- git_diff ---


def test_diff_returns_change_against_ref(git_repo: Path):
    _write(git_repo, Path("foo.txt"), "old\n")
    _commit_all(git_repo)
    _write(git_repo, Path("foo.txt"), "new\n")

    diff = git_diff("HEAD", git_repo)

    assert "@@ -1 +1 @@" in diff


def test_diff_raises_on_unknown_ref(git_repo: Path):
    with pytest.raises(GitError):
        git_diff("does-not-exist", git_repo)


# --- git_ls_untracked ---


def test_ls_untracked_returns_root_relative_paths_regardless_of_cwd(
    git_repo: Path,
):
    _write(git_repo, Path("tracked.txt"), "x\n")
    _commit_all(git_repo)

    subdir = git_repo / "sub"
    subdir.mkdir()
    _write(git_repo, Path("sub") / "untracked.txt", "y\n")

    assert git_ls_untracked(git_repo) == "sub/untracked.txt"
    assert git_ls_untracked(subdir) == "sub/untracked.txt"


# --- _run ---


def test_run_raises_git_error_when_binary_missing():
    with pytest.raises(GitError):
        _run(["definitely-not-a-git"])
