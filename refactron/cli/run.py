"""refactron run — full one-shot pipeline: analyze → queue → verify → apply."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from refactron.core.models import IssueLevel
from refactron.core.pipeline import RefactronPipeline

console = Console()

_LEVEL_MAP = {
    "CRITICAL": IssueLevel.CRITICAL,
    "ERROR": IssueLevel.ERROR,
    "WARNING": IssueLevel.WARNING,
    "INFO": IssueLevel.INFO,
}
_LEVEL_RANK = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 3}


@click.command()
@click.argument("target", type=click.Path(exists=True))
@click.option(
    "--fix-on",
    "fix_on",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO"], case_sensitive=False),
    default="CRITICAL",
    show_default=True,
    help="Queue and fix issues at this level and above",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be fixed without writing any files",
)
@click.option(
    "--no-verify",
    "skip_verify",
    is_flag=True,
    default=False,
    help="Skip VerificationEngine checks (not recommended)",
)
@click.option(
    "--fail-on",
    "fail_on",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO"], case_sensitive=False),
    default=None,
    help="Exit 1 if issues at this level or above remain after fixing",
)
def run(
    target: str,
    fix_on: str,
    dry_run: bool,
    skip_verify: bool,
    fail_on: Optional[str],
) -> None:
    """Run the full Refactron pipeline in one shot.

    \b
    1. Analyze <target>
    2. Queue issues at --fix-on level and above
    3. Apply fixes with verification (unless --dry-run)
    4. Print summary + session ID for rollback

    \b
    Example:
        refactron run src/ --fix-on CRITICAL --dry-run
        refactron run src/ --fix-on WARNING --fail-on ERROR
    """
    target_path = Path(target)
    pipeline = RefactronPipeline(
        project_root=target_path if target_path.is_dir() else target_path.parent
    )

    # Step 1: Analyze
    console.print(f"[bold]Analyzing[/bold] {target_path}...")
    session = pipeline.analyze(target_path)
    console.print(
        f"  {session.total_files} files · {session.total_issues} issues "
        f"({session.issues_by_level.get('CRITICAL', 0)} critical, "
        f"{session.issues_by_level.get('WARNING', 0)} warnings)"
    )

    # Step 2: Queue
    if pipeline._last_result:
        all_issues = [i for fm in pipeline._last_result.file_metrics for i in fm.issues]
        pipeline.queue_issues(session, all_issues, min_level=_LEVEL_MAP[fix_on.upper()])
    queued = len([i for i in session.fix_queue if i.status.value == "pending"])
    console.print(f"  {queued} issues queued at {fix_on}+ level")

    if queued == 0:
        console.print("[green]Nothing to fix.[/green]")
    else:
        # Step 3: Apply
        action = "Previewing" if dry_run else "Applying"
        console.print(f"\n[bold]{action} fixes...[/bold]")
        pipeline.apply(session, dry_run=dry_run, verify=not skip_verify)

        applied = len(session.applied_fixes)
        blocked = len(session.blocked_fixes)

        if dry_run:
            console.print(f"  [yellow]Dry run — {queued} fixes previewed, nothing written[/yellow]")
        else:
            console.print(f"  [green]Applied: {applied}[/green]")
            if blocked:
                console.print(f"  [red]Blocked: {blocked}[/red]")

    console.print(f"\n[dim]Session: {session.session_id}[/dim]")
    if not dry_run and session.applied_fixes:
        console.print(
            f"[dim]To undo: refactron rollback --pipeline-session {session.session_id}[/dim]"
        )

    # --fail-on gate
    if fail_on:
        threshold = _LEVEL_RANK[fail_on.upper()]
        should_fail = any(
            session.issues_by_level.get(lvl, 0) > 0
            for lvl, rank in _LEVEL_RANK.items()
            if rank >= threshold
        )
        if should_fail:
            raise SystemExit(1)
