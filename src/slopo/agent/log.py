from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, TextIO


class LogOpenError(Exception):
    def __init__(self, log_file: Path, original: OSError) -> None:
        self.log_file = log_file
        self.original = original


class AgentLog:
    def __init__(self, file: TextIO) -> None:
        self._file = file

    def write(self, message: str) -> None:
        self._file.write(message + "\n")
        self._file.flush()


@contextmanager
def open_agent_log(log_file: Path, header: str) -> Iterator[AgentLog]:
    try:
        file = log_file.open("a", encoding="utf-8")
    except OSError as e:
        raise LogOpenError(log_file, e)

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"\n==== {timestamp} {header} ====\n")
        file.flush()
        yield AgentLog(file)
    finally:
        file.close()
