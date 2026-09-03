from pathlib import Path

import pytest

from slopo.agent.config import (
    AGENT_CONFIG_VERSION,
    AgentConfigsDirExistsError,
    AgentConfigVersionMismatchError,
    check_version,
    export_configs,
)


def test_accepts_matching_version():
    check_version(AGENT_CONFIG_VERSION)


def test_accepts_none():
    check_version(None)


def test_raises_on_mismatch():
    declared = AGENT_CONFIG_VERSION + 1

    with pytest.raises(AgentConfigVersionMismatchError) as exc_info:
        check_version(declared)

    assert exc_info.value.declared == declared
    assert exc_info.value.expected == AGENT_CONFIG_VERSION


def test_export_configs_copies_bundled_files(tmp_path: Path):
    dest = tmp_path / "slopo-agent-configs"

    export_configs(dest)

    assert any((dest / "claude-code-skills").iterdir())
    assert any((dest / "codex-skills").iterdir())
    assert not (dest / "__init__.py").exists()


def test_export_configs_raises_when_dest_exists(tmp_path: Path):
    dest = tmp_path / "slopo-agent-configs"
    dest.mkdir()

    with pytest.raises(AgentConfigsDirExistsError) as exc_info:
        export_configs(dest)

    assert exc_info.value.path == dest
