"""refactron status — show pipeline session state."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from refactron.core.pipeline_session import FixStatus, SessionStore

console = Console()


@click.command()
@click.option("--session", "session_id", default=None, help="Session ID to inspect")
@click.option(
    "--list", "list_sessions", is_flag=True, default=False, help="List all sessions"
)
@click.option(
    "--project-root",
    default=".",
    help="Project root (where .refactron/ lives)",
)
def status(session_id: Optional[str], list_sessions: bool, project_root: str) -> None:
    """Show the state of a pipeline session."""
    store = SessionStore(root_dir=Path(project_root))

    if list_sessions:
        sessions = store.list_sessions()
        if not sessions:
            console.print("[dim]No sessions found.[/dim]")
            return
        table = Table(title="Pipeline Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Target")
        table.add_column("State")
        table.add_column("Files")
        table.add_column("Issues")
        table.add_column("Created")
        for s in reversed(sessions):
            table.add_row(
                s.session_id,
                s.target,
                s.state.value,
                str(s.total_files),
                str(s.total_issues),
                s.created_at[:19],
            )
        console.print(table)
        return

    session = store.load(session_id) if session_id else store.load_latest()

    if session is None:
        console.print(
            "[dim]No session found. Run [bold]refactron analyze <target>[/bold] first.[/dim]"
        )
        return

    console.print(f"\n[bold]Session:[/bold] {session.session_id}")
    console.print(f"[bold]Target:[/bold]  {session.target}")
    console.print(f"[bold]State:[/bold]   {session.state.value}")
    console.print(f"[bold]Created:[/bold] {session.created_at[:19]}")

    console.print("\n[bold]Analysis[/bold]")
    console.print(f"  Files analyzed: {session.total_files}")
    console.print(f"  Total issues:   {session.total_issues}")
    _STYLES = {"CRITICAL": "bold red", "ERROR": "red", "WARNING": "yellow", "INFO": "cyan"}
    for level in ("CRITICAL", "ERROR", "WARNING", "INFO"):
        count = session.issues_by_level.get(level, 0)
        if count:
            style = _STYLES[level]
            console.print(f"  [{style}]{level}[/{style}]: {count}")

    pending = [i for i in session.fix_queue if i.status == FixStatus.PENDING]
    applied = session.applied_fixes
    blocked = session.blocked_fixes
    skipped = [i for i in session.fix_queue if i.status == FixStatus.SKIPPED]

    if session.fix_queue or applied or blocked:
        console.print("\n[bold]Fixes[/bold]")
        if pending:
            console.print(f"  [yellow]Queued (not yet applied):[/yellow] {len(pending)}")
        if applied:
            console.print(f"  [green]Applied:[/green] {len(applied)}")
        if blocked:
            console.print(f"  [red]Blocked:[/red] {len(blocked)}")
            for b in blocked[:3]:
                console.print(f"    • {b.file_path}:{b.line_number} — {b.block_reason}")
        if skipped:
            console.print(f"  [dim]Skipped (no fixer): {len(skipped)}[/dim]")

    console.print("\n[bold]Next steps[/bold]")
    if pending:
        console.print(
            f"  [dim]refactron autofix --session {session.session_id} --apply[/dim]"
        )
    if applied:
        console.print(
            f"  [dim]refactron rollback --session {session.session_id}[/dim]  (to undo)"
        )
