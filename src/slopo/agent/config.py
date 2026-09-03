import shutil
from importlib.resources import as_file, files
from pathlib import Path


AGENT_CONFIG_VERSION = 1

AGENT_CONFIGS_DIR = Path("slopo-agent-configs")


class AgentConfigVersionMismatchError(Exception):
    def __init__(self, declared: int, expected: int) -> None:
        self.declared = declared
        self.expected = expected


class AgentConfigsDirExistsError(Exception):
    def __init__(self, path: Path) -> None:
        self.path = path


def check_version(declared: int | None) -> None:
    if declared is not None and declared != AGENT_CONFIG_VERSION:
        raise AgentConfigVersionMismatchError(declared, AGENT_CONFIG_VERSION)


def export_configs(dest: Path) -> None:
    if dest.exists():
        raise AgentConfigsDirExistsError(dest)

    bundle = files("slopo.agent.configs")
    with as_file(bundle) as bundle_path:
        shutil.copytree(
            bundle_path,
            dest,
            ignore=shutil.ignore_patterns("__init__.py", "__pycache__"),
        )
