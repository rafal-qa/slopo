import traceback
from dataclasses import dataclass
from pathlib import Path

from slopo.agent.config import (
    AgentConfigsDirExistsError,
    AgentConfigVersionMismatchError,
)
from slopo.agent.log import LogOpenError
from slopo.config import ConfigError, ConfigFileNotFoundError
from slopo.db import (
    ConfigurationMismatchError,
    DatabaseNotFoundError,
    SchemaVersionMismatchError,
)
from slopo.embedding.embeddings import EmbeddingError
from slopo.result.analysis.selection import ClusterNotFoundError
from slopo.result.review.git.commands import GitError
from slopo.result.review.index_check import StaleIndexError


class SourceDirMissingError(Exception):
    def __init__(self, source_dir: Path) -> None:
        self.source_dir = source_dir


class UnembeddedUnitsError(Exception):
    pass


class TooManyUnembeddedForAgentError(Exception):
    pass


class InternalError(Exception):
    def __init__(self, original: BaseException) -> None:
        self.original = original


@dataclass
class ErrorMessages:
    human: str
    agent: str = "Unexpected error."


KNOWN_ERRORS: tuple[type[Exception], ...] = (
    SourceDirMissingError,
    UnembeddedUnitsError,
    TooManyUnembeddedForAgentError,
    ClusterNotFoundError,
    AgentConfigVersionMismatchError,
    AgentConfigsDirExistsError,
    ConfigError,
    ConfigFileNotFoundError,
    DatabaseNotFoundError,
    ConfigurationMismatchError,
    SchemaVersionMismatchError,
    EmbeddingError,
    StaleIndexError,
    GitError,
)


def describe(exc: Exception) -> ErrorMessages:
    match exc:
        case SourceDirMissingError():
            return ErrorMessages(
                human=f"{exc.source_dir} is not a directory.",
            )
        case UnembeddedUnitsError():
            return ErrorMessages(
                human="Some code units have no embeddings. Run `embed` first.",
            )
        case TooManyUnembeddedForAgentError():
            return ErrorMessages(
                human="Too many code units to embed. Run `embed` first.",
                agent="Too many code units to embed. The tool probably wasn't fully initialized.",
            )
        case ClusterNotFoundError():
            human = (
                "No clusters in the report."
                if exc.cluster_hash is None
                else f"No cluster with hash '{exc.cluster_hash}' in the report."
            )
            agent = (
                "No clusters in the report."
                if exc.cluster_hash is None
                else "Cluster not found."
            )
            return ErrorMessages(human=human, agent=agent)
        case AgentConfigVersionMismatchError():
            return ErrorMessages(
                human="Your agent config files are out of date. Replace them with the latest templates.",
                agent="Configuration for coding agent is out of date.",
            )
        case AgentConfigsDirExistsError():
            return ErrorMessages(
                human=f"{exc.path} already exists. Remove it, then re-run.",
            )
        case ConfigFileNotFoundError():
            return ErrorMessages(
                human=f"No config file found at {exc.path}. Run `slopo init` to create one.",
                agent="Configuration file not found. Make sure that the agent CLI is run from the correct directory.",
            )
        case ConfigError():
            return ErrorMessages(
                human=str(exc),
                agent="Loading configuration failed.",
            )
        case DatabaseNotFoundError():
            return ErrorMessages(
                human=f"No data found at {exc.db_file}. Run `index` first.",
                agent="No data in database. The tool wasn't initialized.",
            )
        case ConfigurationMismatchError():
            return ErrorMessages(
                human=(
                    f"Configuration mismatch: {exc.field} was set to '{exc.stored}' when the"
                    f" database was created and cannot be changed (current config: '{exc.current}')"
                ),
                agent="Configuration mismatch.",
            )
        case SchemaVersionMismatchError():
            return ErrorMessages(
                human=(
                    f"Schema version mismatch: database is v{exc.database_version},"
                    f" this version expects v{exc.expected_version}."
                    f" You need to delete slopo.db and create a new one with `index`."
                ),
                agent="Database schema version mismatch.",
            )
        case EmbeddingError():
            return ErrorMessages(
                human=str(exc),
                agent="Embedding failed.",
            )
        case StaleIndexError():
            return ErrorMessages(
                human="Index is out of date. Run `index` and `embed` first.",
            )
        case GitError():
            return ErrorMessages(
                human=f"Git failed: {exc}",
                agent="Git command failed.",
            )
        case InternalError():
            return ErrorMessages(
                human="".join(traceback.format_exception(exc.original)),
                agent="Internal error.",
            )
        case LogOpenError():
            return ErrorMessages(
                human=f"Cannot open log file {exc.log_file}: {exc.original}",
                agent="Cannot open log file.",
            )
    raise ValueError(
        f"describe() called with unknown exception type: {type(exc).__name__}"
    )
