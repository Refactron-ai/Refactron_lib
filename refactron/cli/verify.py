"""
Refactron CLI - Verification Module.
Command to run the Verification Engine on a code change and emit either a
human-readable report or a stable, machine-readable JSON object for CI gates.
"""

from pathlib import Path
from typing import Optional

import click

from refactron.cli.ui import _auth_banner, console
from refactron.verification.engine import VerificationEngine
from refactron.verification.report import (
    format_verification_result,
    format_verification_result_json,
)


@click.command()
@click.argument("target", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--against",
    "-a",
    "candidate",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help=(
        "Path to the proposed/modified version of TARGET. "
        "If omitted, TARGET is verified against itself."
    ),
)
@click.option(
    "--project-root",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="Project root used by the test-suite gate. Defaults to the current directory.",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Refactron config file; its `verification:` section tunes the pipeline "
    "(enabled checks, ordering, test-gate timeout, pytest args).",
)
@click.option(
    "--all-checks",
    is_flag=True,
    default=False,
    help=(
        "Run every check even after one fails (no short-circuit), so all "
        "failure categories surface in a single run. Overrides config."
    ),
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit a stable, machine-readable JSON report instead of formatted text.",
)
def verify(
    target: str,
    candidate: Optional[str],
    project_root: Optional[str],
    config: Optional[str],
    all_checks: bool,
    as_json: bool,
) -> None:
    """
    Verify that a code change is safe to apply.

    TARGET is the file as it currently lives in the project. With --against,
    the proposed new content is checked against it (syntax, import integrity,
    test suite). Exit code is 0 when safe to apply, 1 when blocked — and with
    --json a versioned JSON object is printed for CI dashboards and bots.
    """
    target_path = Path(target)
    original = target_path.read_text(encoding="utf-8")
    transformed = Path(candidate).read_text(encoding="utf-8") if candidate else original

    # A config file's `verification:` section tunes the pipeline; without one
    # the engine falls back to its built-in defaults.
    verification_cfg = None
    if config:
        from refactron.core.config import RefactronConfig

        verification_cfg = RefactronConfig.from_file(Path(config)).verification

    root = Path(project_root) if project_root else Path.cwd()
    engine = VerificationEngine(project_root=root, config=verification_cfg)
    # --all-checks forces a full run; otherwise honour the configured value.
    result = engine.verify(
        original,
        transformed,
        target_path,
        short_circuit=False if all_checks else None,
    )

    if as_json:
        # JSON mode prints only the JSON object so consumers can parse stdout.
        click.echo(format_verification_result_json(result))
    else:
        console.print()
        _auth_banner("Verification")
        format_verification_result(result, console)
"""refactron verify <file> --against <original> — standalone verification command."""

from pathlib import Path

import click
from rich.console import Console

from refactron.verification.engine import VerificationEngine
from refactron.verification.report import format_verification_result

console = Console()


@click.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--against",
    "original",
    required=True,
    type=click.Path(exists=True),
    help="Path to the original (unmodified) file to compare against",
)
@click.option(
    "--project-root",
    type=click.Path(exists=True),
    default=None,
    help="Project root for test discovery (defaults to file's directory)",
)
def verify(file: str, original: str, project_root: str) -> None:
    """Verify that a transformed file is safe to apply.

    FILE is the transformed version. --against is the original.

    Runs all 3 verification checks (syntax, import integrity, test suite gate)
    and exits 0 if safe to apply, 1 if blocked.

    \b
    Example (CI usage):
        refactron verify new_version.py --against original.py
    """
    file_path = Path(file)
    original_path = Path(original)
    root = Path(project_root) if project_root else file_path.parent

    transformed_code = file_path.read_text(encoding="utf-8")
    original_code = original_path.read_text(encoding="utf-8")

    engine = VerificationEngine(project_root=root)
    result = engine.verify(original_code, transformed_code, file_path)

    format_verification_result(result, console)

    raise SystemExit(0 if result.safe_to_apply else 1)
