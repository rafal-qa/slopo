import platform
from dataclasses import fields
from pathlib import Path
from importlib.metadata import version

import sqlite3
import typer
from dotenv import load_dotenv

from slopo.config import (
    Config,
    ConfigError,
    load_config,
    mask_api_key,
    write_config_template,
)
from slopo.db import (
    ConfigurationMismatchError,
    DatabaseNotFoundError,
    SchemaVersionMismatchError,
    create_db,
    open_db,
    verify_source_dir,
)
from slopo.indexing.command import run_index
from slopo.embedding.command import run_embed
from slopo.embedding.embeddings import EmbeddingError
from slopo.embedding.db import count_unembedded_units
from slopo.analysis.command import run_analyze

load_dotenv()

app = typer.Typer(
    help="Embedding-based code duplication detector",
    no_args_is_help=True,
    add_completion=False,
)

_DEFAULT_CONFIG = Path("slopo.conf.yaml")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"Slopo {version('slopo')}")
        typer.echo(f"Python {platform.python_version()}")
        typer.echo(f"SQLite {sqlite3.sqlite_version}")
        raise typer.Exit()


@app.callback()
def _main(
    ctx: typer.Context,
    config_path: Path = typer.Option(
        _DEFAULT_CONFIG, "--config", help="Path to the configuration file"
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
    except ConfigError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    typer.echo(
        f"Created config template at {path}. Edit it before running other commands."
    )


@app.command(name="show-config")
def show_config(ctx: typer.Context) -> None:
    """Validate configuration and show all values."""
    cfg = _load_config_or_exit(ctx)
    for f in fields(cfg):
        value = getattr(cfg, f.name)
        if value is None:
            value = "<unset>"
        elif f.name == "embedding_api_key":
            value = mask_api_key(value)
        typer.echo(f"{f.name}: {value}")


@app.command()
def index(ctx: typer.Context) -> None:
    """Scan a directory and store parsed code units."""
    cfg = _load_config_or_exit(ctx)

    if not cfg.source_dir.is_dir():
        typer.echo(f"Error: {cfg.source_dir} is not a directory", err=True)
        raise typer.Exit(1)

    if cfg.db_file.exists():
        conn = _open_existing_db_or_exit(cfg)
        try:
            verify_source_dir(conn, cfg.source_dir)
        except ConfigurationMismatchError as e:
            typer.echo(_configuration_mismatch_message(e), err=True)
            raise typer.Exit(1)
    else:
        conn = create_db(cfg)

    run_index(conn, cfg, typer.echo)


@app.command()
def embed(ctx: typer.Context) -> None:
    """Compute embeddings for indexed code units."""
    cfg = _load_config_or_exit(ctx)
    conn = _open_existing_db_or_exit(cfg)
    try:
        run_embed(conn, cfg, typer.echo)
    except EmbeddingError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def analyze(ctx: typer.Context) -> None:
    """Produce a Markdown report of similar code clusters."""
    cfg = _load_config_or_exit(ctx)
    conn = _open_existing_db_or_exit(cfg)

    if count_unembedded_units(conn) > 0:
        typer.echo(
            "Error: Some code units have no embeddings. Run `embed` first.",
            err=True,
        )
        raise typer.Exit(1)

    run_analyze(conn, cfg, typer.echo)


def main() -> None:
    app()


def _config_path(ctx: typer.Context) -> Path:
    return ctx.obj["config_path"]


def _load_config_or_exit(ctx: typer.Context) -> Config:
    try:
        return load_config(_config_path(ctx))
    except ConfigError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def _open_existing_db_or_exit(cfg: Config) -> sqlite3.Connection:
    try:
        return open_db(cfg)
    except DatabaseNotFoundError:
        typer.echo(
            f"Error: no indexed data found at {cfg.db_file}. Run `slopo index` first.",
            err=True,
        )
        raise typer.Exit(1)
    except ConfigurationMismatchError as e:
        typer.echo(_configuration_mismatch_message(e), err=True)
        raise typer.Exit(1)
    except SchemaVersionMismatchError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def _configuration_mismatch_message(e: ConfigurationMismatchError) -> str:
    return (
        f"Error: configuration mismatch: {e.field} was set to {e.stored!r} when the"
        f" database was created and cannot be changed (current config: {e.current!r})"
    )
