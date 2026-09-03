import platform
from dataclasses import fields
from pathlib import Path
from importlib.metadata import version

import sqlite3
from typing import NoReturn

import typer
from dotenv import load_dotenv

from slopo.agent.config import (
    AGENT_CONFIGS_DIR,
    check_version as check_agent_config_version,
    export_configs,
)
from slopo.agent.log import AgentLog, open_agent_log, LogOpenError
from slopo.config import (
    ConfigError,
    ConfigFileNotFoundError,
    load_config,
    mask_api_key,
    write_config_template,
)
from slopo.db import create_db, open_db
from slopo.indexing.command import run_index
from slopo.embedding.command import run_embed
from slopo.embedding.db import count_unembedded_units
from slopo.result.analysis.command import run_analyze
from slopo.result.analysis.selection import select_cluster
from slopo.result.analysis.text import format_analyze
from slopo.result.report.filesystem import write_analyze_report, write_review_report
from slopo.result.review.command import run_review
from slopo.result.review.git.commands import GitError, git_version
from slopo.result.review.text import format_review
from slopo.errors import (
    KNOWN_ERRORS,
    InternalError,
    SourceDirMissingError,
    TooManyUnembeddedForAgentError,
    UnembeddedUnitsError,
    describe,
)

load_dotenv()

app = typer.Typer(
    help="Find similar code using embeddings.",
    no_args_is_help=True,
    add_completion=False,
)

_DEFAULT_CONFIG = Path("slopo.conf.yaml")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"Slopo {version('slopo')}")
        typer.echo(f"Python {platform.python_version()}")
        typer.echo(f"SQLite {sqlite3.sqlite_version}")
        try:
            typer.echo(f"Git: {git_version()}")
        except GitError:
            typer.echo("Git: not detected")
        raise typer.Exit()


@app.callback()
def _main(
    ctx: typer.Context,
    config_path: Path = typer.Option(
        _DEFAULT_CONFIG, "--config", help="Configuration file to use."
    ),
    _version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    ctx.obj = {"config_path": config_path}


@app.command()
def init(ctx: typer.Context) -> None:
    """Create a configuration file template."""
    path = _config_path(ctx)

    try:
        write_config_template(path)
    except KNOWN_ERRORS as e:
        _exit(e)

    typer.echo(
        f"Created config template at {path}. Edit it before running other commands."
    )


@app.command(name="show-config")
def show_config(ctx: typer.Context) -> None:
    """Validate and display configuration values."""
    try:
        cfg = load_config(_config_path(ctx))
    except KNOWN_ERRORS as e:
        _exit(e)

    for f in fields(cfg):
        value = getattr(cfg, f.name)
        if f.name == "embedding_params":
            if not value:
                typer.echo(f"{f.name}: <unset>")
            else:
                typer.echo(f"{f.name}:")
                for key, item in value.items():
                    typer.echo(f"  {key}: {item}")
            continue
        if value is None or value == []:
            value = "<unset>"
        elif f.name == "embedding_api_key":
            value = mask_api_key(value)
        typer.echo(f"{f.name}: {value}")


@app.command()
def index(ctx: typer.Context) -> None:
    """Update the code index."""
    try:
        cfg = load_config(_config_path(ctx))

        if not cfg.source_dir.is_dir():
            raise SourceDirMissingError(cfg.source_dir)

        if cfg.db_file.exists():
            conn = open_db(cfg)
        else:
            conn = create_db(cfg)

        run_index(conn, cfg, typer.echo)
    except KNOWN_ERRORS as e:
        _exit(e)


@app.command()
def embed(ctx: typer.Context) -> None:
    """Generate embeddings for indexed code."""
    try:
        cfg = load_config(_config_path(ctx))
        conn = open_db(cfg)
        run_embed(conn, cfg, typer.echo)
    except KNOWN_ERRORS as e:
        _exit(e)


@app.command()
def analyze(ctx: typer.Context) -> None:
    """Find similar code across the codebase."""
    try:
        cfg = load_config(_config_path(ctx))
        conn = open_db(cfg)

        if count_unembedded_units(conn) > 0:
            raise UnembeddedUnitsError

        result = run_analyze(conn, cfg, typer.echo)
        if result is not None:
            write_analyze_report(result.clusters, result.units, cfg.report_dir)
            typer.echo(f"Report written to {cfg.report_dir} directory.")
    except KNOWN_ERRORS as e:
        _exit(e)


@app.command()
def review(
    ctx: typer.Context,
    base: str = typer.Option(
        "HEAD", "--base", help="Git ref to compare the working tree against."
    ),
) -> None:
    """Find similar code involving Git changes."""
    if base == "":
        base = "HEAD"
    try:
        cfg = load_config(_config_path(ctx))
        conn = open_db(cfg)

        if count_unembedded_units(conn) > 0:
            raise UnembeddedUnitsError

        result = run_review(conn, cfg, base, typer.echo)
        if result is not None:
            write_review_report(result, cfg.report_dir)
            typer.echo(f"Report written to {cfg.report_dir} directory.")
    except KNOWN_ERRORS as e:
        _exit(e)


@app.command(name="agent-configs")
def agent_configs() -> None:
    """Export coding agents skill configurations."""
    try:
        export_configs(AGENT_CONFIGS_DIR)
    except KNOWN_ERRORS as e:
        _exit(e)

    typer.echo(
        f"Exported agent configurations to {AGENT_CONFIGS_DIR}."
        " Move what you need into your coding agent's skill location, then remove the directory."
    )


@app.command(name="agent-review")
def agent_review(
    ctx: typer.Context,
    base: str = typer.Option(
        "HEAD", "--base", help="Git ref to compare the working tree against."
    ),
    config_version: int | None = typer.Option(
        None, "--config-version", help="Agent config version."
    ),
) -> None:
    """Run index, embed, and review as a single operation for coding agents."""
    if base == "":
        base = "HEAD"
    try:
        cfg = load_config(_config_path(ctx))
        log_cm = open_agent_log(
            cfg.agent_log_file,
            f"agent-review base={base} config-version={config_version}",
        )
    except (ConfigError, ConfigFileNotFoundError, LogOpenError) as e:
        _exit_agent(e)
    else:
        with log_cm as log:
            try:
                check_agent_config_version(config_version)

                conn = open_db(cfg)

                if count_unembedded_units(conn) > 1000:
                    raise TooManyUnembeddedForAgentError

                log.write("> index")
                run_index(conn, cfg, log.write)

                log.write("> embed")
                run_embed(conn, cfg, log.write)

                log.write("> review")
                result = run_review(conn, cfg, base, log.write)
                if result is None:
                    typer.echo("No duplicates found")
                else:
                    typer.echo(format_review(result, cfg.source_dir))
            except KNOWN_ERRORS as e:
                _exit_agent_with_log(e, log)
            except Exception as e:
                _exit_agent_with_log(InternalError(e), log)


@app.command(name="agent-analyze")
def agent_analyze(
    ctx: typer.Context,
    single: bool = typer.Option(
        False, "--single", help="Report only a single cluster."
    ),
    cluster: str | None = typer.Option(
        None, "--cluster", help="Hash of the cluster to report."
    ),
    config_version: int | None = typer.Option(
        None, "--config-version", help="Agent config version."
    ),
) -> None:
    """Run index, embed, and analyze as a single operation for coding agents."""
    cluster = cluster or None
    if cluster is not None and not single:
        raise typer.BadParameter("--cluster requires --single.")

    try:
        cfg = load_config(_config_path(ctx))
        h_cluster = f" cluster={cluster}" if single else ""
        log_cm = open_agent_log(
            cfg.agent_log_file,
            f"agent-analyze single={single}{h_cluster} config-version={config_version}",
        )
    except (ConfigError, ConfigFileNotFoundError, LogOpenError) as e:
        _exit_agent(e)
    else:
        with log_cm as log:
            try:
                check_agent_config_version(config_version)

                conn = open_db(cfg)

                if count_unembedded_units(conn) > 1000:
                    raise TooManyUnembeddedForAgentError

                log.write("> index")
                run_index(conn, cfg, log.write)

                log.write("> embed")
                run_embed(conn, cfg, log.write)

                log.write("> analyze")
                result = run_analyze(conn, cfg, log.write)

                if single:
                    result = select_cluster(result, cluster)

                if result is None:
                    typer.echo("No duplicates found")
                else:
                    typer.echo(f"Ignore file: {cfg.ignore_file.resolve()}\n")
                    typer.echo(format_analyze(result, cfg.source_dir))
            except KNOWN_ERRORS as e:
                _exit_agent_with_log(e, log)
            except Exception as e:
                _exit_agent_with_log(InternalError(e), log)


def main() -> None:
    app()


def _config_path(ctx: typer.Context) -> Path:
    return ctx.obj["config_path"]


def _exit(exc: Exception) -> NoReturn:
    msg = describe(exc)
    typer.echo(f"Error: {msg.human}", err=True)
    raise typer.Exit(1)


def _exit_agent(exc: Exception) -> NoReturn:
    msg = describe(exc)
    typer.echo(f"Error: {msg.agent}", err=True)
    raise typer.Exit(1)


def _exit_agent_with_log(exc: Exception, log: AgentLog) -> NoReturn:
    msg = describe(exc)
    log.write(f"Error: {msg.human}")
    typer.echo(f"Error: {msg.agent}", err=True)
    raise typer.Exit(1)
