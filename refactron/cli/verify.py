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
