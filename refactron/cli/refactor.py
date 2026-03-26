"""
Refactron CLI - Refactoring Module.
Commands for refactoring code, autofixing issues, and managing rollbacks.
"""

from pathlib import Path
from typing import Optional

import click
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from refactron import Refactron
from refactron.autofix.engine import AutoFixEngine
from refactron.autofix.models import FixRiskLevel
from refactron.cli.ui import (
    _auth_banner,
    _collect_feedback_interactive,
    _confirm_apply_mode,
    _create_refactor_table,
    _print_file_count,
    _print_refactor_filters,
    _print_refactor_messages,
    _record_applied_operations,
    console,
)
from refactron.cli.utils import _load_config, _setup_logging, _validate_path
from refactron.core.backup import BackupRollbackSystem
from refactron.core.workspace import WorkspaceManager
from refactron.llm.models import SuggestionStatus
from refactron.llm.orchestrator import LLMOrchestrator
from refactron.rag.retriever import ContextRetriever


@click.command()
@click.argument("target", type=click.Path(exists=True), required=False)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--profile",
    "-p",
    type=click.Choice(["dev", "staging", "prod"], case_sensitive=False),
    help=(
        "Named configuration profile to use (dev, staging, prod). "
        "Profiles typically group config defaults; if both --profile and "
        "--environment are set, the environment determines the final "
        "effective configuration."
    ),
)
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["dev", "staging", "prod"], case_sensitive=False),
    help=(
        "Target runtime environment (dev, staging, prod). When both "
        "--profile and --environment are provided, the environment "
        "overrides the selected profile."
    ),
)
@click.option(
    "--preview/--apply",
    default=True,
    help="Preview changes or apply them",
)
@click.option(
    "--types",
    "-t",
    multiple=True,
    help="Specific refactoring types to apply",
)
@click.option(
    "--feedback/--no-feedback",
    default=False,
    help="Collect interactive feedback on refactoring suggestions",
)
def refactor(
    target: Optional[str],
    config: Optional[str],
    profile: Optional[str],
    environment: Optional[str],
    preview: bool,
    types: tuple,
    feedback: bool,
) -> None:
    """
    Refactor code with intelligent transformations.

    TARGET: Path to file or directory to refactor (optional if workspace is connected)
    """
    # Setup logging
    _setup_logging()

    console.print()
    _auth_banner("Refactoring")
    console.print()

    # Determine target path - use workspace if not provided
    if not target:
        workspace_mgr = WorkspaceManager()
        current_workspace = workspace_mgr.get_workspace_by_path(str(Path.cwd()))

        if current_workspace:
            target = current_workspace.local_path
            console.print(
                f"[dim]Using connected workspace: {current_workspace.repo_full_name}[/dim]\n"
            )
        else:
            console.print(
                "[red]Error: No target specified and current directory is not a connected workspace.[/red]\n\n"  # noqa: E501
                "[dim]Options:[/dim]\n"
                "  1. Specify a path: refactron refactor /path/to/code\n"
                "  2. Connect a workspace: refactron repo connect <repo-name>\n"
                "  3. Navigate to a connected workspace directory\n"
            )
            raise SystemExit(1)

    # Setup
    target_path = _validate_path(target)
    cfg = _load_config(config, profile, environment)
    _print_refactor_filters(types)
    _confirm_apply_mode(preview)

    # Create backup before applying changes (only in apply mode)
    session_id = None
    if not preview and cfg.backup_enabled:
        try:
            # Detect project root to ensure backups are stored in a consistent location
            # (usually the directory containing .git or .refactron.yaml)
            refactron_instance = Refactron(cfg)
            backup_root = refactron_instance.detect_project_root(target_path)

            backup_system = BackupRollbackSystem(backup_root)

            if target_path.is_file():
                files = [target_path]
            else:
                files = refactron_instance.get_python_files(target_path)

            if files:
                session_id, failed_files = backup_system.prepare_for_refactoring(
                    files=files,
                    description=f"refactoring {target}",
                    create_git_commit=backup_system.git.is_git_repo(),
                )
                console.print(f"[dim]Backup created: {session_id}[/dim]")
                if failed_files:
                    console.print(
                        f"[yellow]{len(failed_files)} file(s) could not be backed up[/yellow]"
                    )
        except (OSError, PermissionError) as e:
            console.print(f"[yellow]Backup creation failed (I/O error): {e}[/yellow]")
            if not click.confirm("Continue without backup?"):
                raise SystemExit(0)
        except Exception as e:
            console.print(f"[yellow]Backup creation failed: {type(e).__name__}: {e}[/yellow]")
            if not click.confirm("Continue without backup?"):
                raise SystemExit(0)

    # Run refactoring
    try:
        with console.status("[primary]Analyzing and generating refactorings...[/primary]"):
            refactron = Refactron(cfg)
            result = refactron.refactor(
                target,
                preview=preview,
                operation_types=list(types) if types else None,
            )
    except Exception as e:
        console.print(f"[red]Refactoring failed: {e}[/red]")
        raise SystemExit(1)

    # Display results
    summary = result.summary()
    console.print(_create_refactor_table(summary))
    console.print()

    _print_refactor_messages(summary, preview)

    if result.operations:
        # Show ranking info if available
        ranked_count = sum(1 for op in result.operations if "ranking_score" in op.metadata)
        if ranked_count > 0:
            console.print(f"[dim]{ranked_count} operations ranked by learned patterns[/dim]\n")

        console.print("[bold]Refactoring Operations:[/bold]\n")
        console.print(result.show_diff())

        # Record feedback
        if not preview:
            # Apply changes to disk
            if result.apply():
                console.print("[green]Successfully applied refactoring changes.[/green]")
            else:
                console.print("[red]Failed to apply some refactoring changes.[/red]")

            # Auto-record as accepted when applying changes
            _record_applied_operations(refactron, result)
        elif feedback:
            # Interactive feedback collection in preview mode
            _collect_feedback_interactive(refactron, result)

    if session_id and not preview:
        console.print("\n[dim]Tip: Run 'refactron rollback' to undo these changes[/dim]")


@click.command()
@click.argument("target", type=click.Path(exists=True))
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--profile",
    "-p",
    type=click.Choice(["dev", "staging", "prod"], case_sensitive=False),
    help=(
        "Named configuration profile to use (dev, staging, prod). "
        "Profiles typically group config defaults; if both --profile and "
        "--environment are set, the environment determines the final "
        "effective configuration."
    ),
)
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["dev", "staging", "prod"], case_sensitive=False),
    help=(
        "Target runtime environment (dev, staging, prod). When both "
        "--profile and --environment are provided, the environment "
        "overrides the selected profile."
    ),
)
@click.option(
    "--preview/--apply",
    default=True,
    help="Preview fixes or apply them",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show a unified diff of what would change — writes nothing to disk",
)
@click.option(
    "--safety-level",
    "-s",
    type=click.Choice(["safe", "low", "moderate", "high"], case_sensitive=False),
    default="safe",
    help="Maximum risk level for automatic fixes",
)
@click.option(
    "--verify",
    is_flag=True,
    default=False,
    help="Run verification checks (syntax, imports, tests) before applying fixes",
)
def autofix(
    target: str,
    config: Optional[str],
    profile: Optional[str],
    environment: Optional[str],
    preview: bool,
    dry_run: bool,
    safety_level: str,
    verify: bool,
) -> None:
    """
    Automatically fix code issues (Phase 3 feature).

    TARGET: Path to file or directory to fix

    Examples:
      refactron autofix myfile.py --preview
      refactron autofix myproject/ --apply --safety-level moderate
    """
    console.print()
    _auth_banner("Auto-fix")
    console.print()

    # Setup
    target_path = _validate_path(target)
    _load_config(config, profile, environment)
    _print_file_count(target_path)

    # Map safety level
    safety_map = {
        "safe": FixRiskLevel.SAFE,
        "low": FixRiskLevel.LOW,
        "moderate": FixRiskLevel.MODERATE,
        "high": FixRiskLevel.HIGH,
    }
    safety = safety_map[safety_level.lower()]

    # Initialize auto-fix engine
    engine = AutoFixEngine(safety_level=safety)

    # --dry-run implies preview (no writes)
    if dry_run or preview:
        console.print("[warning]Dry-run mode: No changes will be written to disk[/warning]\n")
    else:
        console.print("[success]Apply mode: Changes will be written to files[/success]\n")

    console.print(f"[secondary]Safety level: {safety_level}[/secondary]")
    console.print(f"[secondary]Available fixers: {len(engine.fixers)}[/secondary]\n")

    # Display available fixers
    console.print("[primary bold]Available Auto-fixes:[/primary bold]\n")
    for fixer_name, fixer in engine.fixers.items():
        if fixer.risk_score == 0.0:
            risk_label = "[success]LOW[/success]"
        elif fixer.risk_score < 0.5:
            risk_label = "[warning]MED[/warning]"
        else:
            risk_label = "[error]HIGH[/error]"
        console.print(f"{risk_label} {fixer_name} (risk: {fixer.risk_score:.1f})")

    console.print(
        "\n[secondary]Tip: Auto-fix requires analyzed issues. Integration with analyzers "
        "coming soon![/secondary]"
    )
    console.print(
        "[secondary]For now, use 'refactron analyze' to find issues, then 'refactron refactor' "
        "to fix them.[/secondary]"
    )


@click.command()
@click.argument("session_id", required=False)
@click.option(
    "--session",
    "-s",
    type=str,
    default=None,
    help="Specific session ID to rollback (deprecated, use argument instead)",
)
@click.option(
    "--use-git",
    is_flag=True,
    default=False,
    help="Use Git rollback instead of file backup",
)
@click.option(
    "--list",
    "list_sessions",
    is_flag=True,
    default=False,
    help="List all backup sessions",
)
@click.option(
    "--clear",
    is_flag=True,
    default=False,
    help="Clear all backup sessions",
)
def rollback(
    session_id: Optional[str],
    session: Optional[str],
    use_git: bool,
    list_sessions: bool,
    clear: bool,
) -> None:
    """
    Rollback refactoring changes to restore original files.

    By default, restores files from the latest backup session.

    Arguments:
        SESSION_ID: Optional specific session ID to rollback.

    Examples:
      refactron rollback              # Rollback latest session
      refactron rollback session_123  # Rollback specific session
      refactron rollback --list       # List all backup sessions
      refactron rollback --use-git    # Use Git rollback
      refactron rollback --clear      # Clear all backups
    """
    # Support both argument and option for session
    target_session = session_id or session
    console.print("\n🔄 [bold blue]Refactron Rollback[/bold blue]\n")

    system = BackupRollbackSystem()

    # If we appear to be in a subdirectory of a project, try to find the root
    # so we can find the centralized backups directory.
    if not system.list_sessions():
        # Quick check for markers up the tree
        current = Path.cwd()
        for _ in range(10):
            if (current / ".refactron" / "backups").exists():
                system = BackupRollbackSystem(current)
                break
            if (current / ".git").exists() or (current / ".refactron.yaml").exists():
                system = BackupRollbackSystem(current)
                break
            if current.parent == current:
                break
            current = current.parent

    if list_sessions:
        sessions = system.list_sessions()
        if not sessions:
            console.print("[yellow]No backup sessions found.[/yellow]")
            return

        table = Table(
            title="Backup Sessions",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Session ID", style="cyan")
        table.add_column("Timestamp", style="green")
        table.add_column("Files", justify="right")
        table.add_column("Git Commit", style="dim")
        table.add_column("Description")

        for sess in sessions:
            git_commit = sess.get("git_commit", "")
            if git_commit:
                git_commit = git_commit[:8] + "..."
            table.add_row(
                sess["id"],
                sess["timestamp"],
                str(len(sess["files"])),
                git_commit or "N/A",
                sess.get("description", "")[:30],
            )

        console.print(table)
        return

    if clear:
        if not click.confirm("Are you sure you want to clear all backup sessions?"):
            return

        count = system.clear_all()
        console.print(f"[success]Cleared {count} backup session(s).[/success]")
        return

    sessions = system.list_sessions()
    if not sessions:
        console.print("[yellow]No backup sessions found.[/yellow]")
        console.print("[dim]Tip: Backups are created automatically when using --apply mode.[/dim]")
        return

    if target_session:
        sess = system.backup_manager.get_session(target_session)
        if not sess:
            console.print(f"[error]Session not found: {target_session}[/error]")
            console.print("[dim]Use 'refactron rollback --list' to see available sessions.[/dim]")
            raise SystemExit(1)
        console.print(f"[dim]Rolling back session: {target_session}[/dim]")
        console.print(f"[dim]Files to restore: {len(sess['files'])}[/dim]")
    else:
        latest = sessions[-1]
        console.print(f"[dim]Rolling back latest session: {latest['id']}[/dim]")
        console.print(f"[dim]Files to restore: {len(latest['files'])}[/dim]")

    if use_git:
        console.print("[dim]Using Git rollback...[/dim]")
    else:
        console.print("[dim]Using file backup rollback...[/dim]")

    console.print(
        "\n[warning]This will overwrite your current files with backup versions.[/warning]"
    )
    if not click.confirm("Are you sure you want to proceed with rollback?"):
        console.print("[yellow]Rollback cancelled.[/yellow]")
        return

    result = system.rollback(session_id=target_session, use_git=use_git)

    if result["success"]:
        console.print(f"\n[success]{result['message']}[/success]")
        if result.get("files_restored"):
            console.print(f"[dim]Files restored: {result['files_restored']}[/dim]")
        if result.get("failed_files"):
            console.print(
                f"[warning]Failed to restore: {', '.join(result['failed_files'])}[/warning]"
            )
    else:
        console.print(f"\n[red]Rollback failed: {result['message']}[/red]")
        raise SystemExit(1)


@click.command()
@click.argument("target", type=click.Path(exists=True))
@click.option(
    "--apply/--no-apply",
    default=False,
    help="Apply the documentation changes to the file",
)
@click.option(
    "--interactive/--no-interactive",
    default=True,
    help="Use interactive mode for apply",
)
def document(target: str, apply: bool, interactive: bool) -> None:
    """
    Generate Google-style docstrings for a Python file.

    Uses AI to analyze code and add comprehensive documentation.
    """
    console.print()
    _auth_banner("AI Documentation")
    console.print()

    # Setup
    cfg = _load_config(None)
    _setup_logging()

    target_path = Path(target).resolve()

    if not target_path.is_file():
        console.print("[red]Error: Please specify a file, not a directory.[/red]")
        return

    refactron_instance = Refactron(cfg)
    workspace_path = refactron_instance.detect_project_root(target_path)

    console.print(f"[bold]Documenting:[/bold] {target_path}")

    # Initialize components
    try:
        retriever = ContextRetriever(workspace_path)
    except Exception:
        console.print(
            "[yellow]Warning: RAG index not found. Context retrieval will be limited.[/yellow]"
        )
        retriever = None

    orchestrator = LLMOrchestrator(retriever=retriever)

    # Generate
    code = target_path.read_text(encoding="utf-8")

    with console.status("[bold cyan]Generating documentation...[/bold cyan]"):
        suggestion = orchestrator.generate_documentation(code, file_path=str(target_path))

    if suggestion.status == SuggestionStatus.FAILED:
        console.print(f"[red]Generation Failed:[/red] {suggestion.explanation}")
        return

    doc_path = target_path.with_name(f"{target_path.stem}_doc.md")

    console.print()
    console.print(
        Panel(
            Markdown(suggestion.explanation),
            title=f"Documentation Plan ({suggestion.model_name})",
            border_style="blue",
        )
    )

    console.print(
        Panel(
            Markdown(suggestion.proposed_code),
            title=f"Preview: {doc_path.name}",
            style="on #1e1e1e",
        )
    )

    console.print(f"[dim]Confidence: {suggestion.confidence_score:.2f}[/dim]")
    console.print()

    # Apply
    if apply:
        if interactive:
            if not click.confirm(
                f"Do you want to create external documentation at {doc_path.name}?"
            ):
                console.print("[yellow]Changes cancelled.[/yellow]")
                return

        try:
            # Write new file (no backup needed for new file creation)
            doc_path.write_text(suggestion.proposed_code, encoding="utf-8")
            console.print(
                f"[green bold]Successfully created documentation: {doc_path}[/green bold]"
            )

        except Exception as e:
            console.print(f"[red]Failed to create documentation: {e}[/red]")
