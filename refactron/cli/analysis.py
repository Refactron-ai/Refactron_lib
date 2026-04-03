"""
Refactron CLI - Analysis Module.
Commands for analyzing code, generating reports, and metrics.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel

from refactron import Refactron
from refactron.cli.ui import (
    _auth_banner,
    _create_summary_table,
    _interactive_file_selector,
    _interactive_issue_viewer,
    _print_detailed_issues,
    _print_file_count,
    _print_helpful_tips,
    _print_status_messages,
    console,
)
from refactron.cli.utils import _load_config, _setup_logging, _validate_path
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel
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
    "--detailed/--summary",
    default=True,
    help="Show detailed or summary report",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    help="Set log level",
)
@click.option(
    "--log-format",
    type=click.Choice(["json", "text"], case_sensitive=False),
    help="Set log format (json for CI/CD, text for console)",
)
@click.option(
    "--metrics/--no-metrics",
    default=None,
    help="Enable or disable metrics collection",
)
@click.option(
    "--show-metrics",
    is_flag=True,
    help="Show metrics summary after analysis",
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
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable incremental analysis cache — re-analyze all files from scratch",
)
@click.option(
    "--no-interactive",
    is_flag=True,
    default=False,
    help="Disable interactive mode — dump all issues (for CI/CD or piped output)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format: text (default) or json (for CI/CD scripts)",
)
@click.option(
    "--fail-on",
    "fail_on",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO"], case_sensitive=False),
    default=None,
    help="Exit 1 if any issues at this level or above exist (for CI quality gates)",
)
def analyze(
    target: Optional[str],
    config: Optional[str],
    detailed: bool,
    log_level: Optional[str],
    log_format: Optional[str],
    metrics: Optional[bool],
    show_metrics: bool,
    profile: Optional[str],
    environment: Optional[str],
    no_cache: bool,
    no_interactive: bool,
    output_format: str = "text",
    fail_on: Optional[str] = None,
) -> None:
    """
    Analyze code for issues and technical debt.

    TARGET: Path to file or directory to analyze (optional if workspace is connected)
    """
    # Setup logging
    _setup_logging()

    if output_format != "json":
        console.print()
        _auth_banner("Analysis")
        console.print()

    # Determine target path - use workspace if not provided
    if not target:
        workspace_mgr = WorkspaceManager()
        current_workspace = workspace_mgr.get_workspace_by_path(str(Path.cwd()))

        if current_workspace:
            console.print(f"[dim]Connected workspace: {current_workspace.repo_full_name}[/dim]")

            # Show interactive file selector
            workspace_root = Path(current_workspace.local_path)
            target_path = _interactive_file_selector(workspace_root)
            target = str(target_path)
        else:
            console.print(
                (
                    "[red]Error: No target specified and current directory "
                    "is not a connected workspace.[/red]\n\n"
                    "[dim]Options:[/dim]\n"
                    "  1. Specify a path: refactron analyze /path/to/code\n"
                    "  2. Connect a workspace: refactron repo connect <repo-name>\n"
                    "  3. Navigate to a connected workspace directory\n"
                )
            )
            raise SystemExit(1)
    else:
        # Path explicitly provided, validate and use it
        target_path = _validate_path(target)

    # Setup (only if not already set by interactive selector)
    if "target_path" not in locals():
        target_path = _validate_path(target)
    cfg = _load_config(config, profile, environment)

    # Override config with CLI options
    if log_level:
        cfg.log_level = log_level
        logging.getLogger("refactron").setLevel(getattr(logging, log_level.upper()))
    if log_format:
        cfg.log_format = log_format
    if metrics is not None:
        cfg.enable_metrics = metrics
    if no_cache:
        cfg.enable_incremental_analysis = False

    if output_format != "json":
        _print_file_count(target_path)

    # Run analysis
    try:
        if output_format != "json":
            with console.status("[primary]Analyzing code...[/primary]"):
                refactron = Refactron(cfg)
                result = refactron.analyze(target)
        else:
            refactron = Refactron(cfg)
            result = refactron.analyze(target)
    except Exception as e:
        if output_format == "json":
            import json as _json_err

            click.echo(_json_err.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Analysis failed: {e}[/red]")
            console.print("[dim]Tip: Check if all files have valid Python syntax[/dim]")
        raise SystemExit(1)

    # Display results
    summary = result.summary()

    # JSON format — output raw JSON and exit immediately
    if output_format == "json":
        import json as _json

        issues_data = [
            {
                "level": issue.level.value.upper(),
                "category": issue.category.value,
                "message": issue.message,
                "file": str(issue.file_path),
                "line": issue.line_number,
                "column": issue.column,
            }
            for issue in result.all_issues
        ]
        payload = {**summary, "issues": issues_data}
        click.echo(_json.dumps(payload, indent=2))
        raise SystemExit(1 if summary["critical"] > 0 else 0)

    use_interactive = sys.stdout.isatty() and not no_interactive

    if use_interactive:
        _interactive_issue_viewer(result, target_path)
    else:
        # Non-interactive: grouped dump for CI/CD or piped output
        console.print(_create_summary_table(summary))
        console.print()

        _print_status_messages(summary)

        if detailed and result.all_issues:
            _print_detailed_issues(result)

        _print_helpful_tips(summary, detailed)

    # Show metrics if requested
    if show_metrics and cfg.enable_metrics:
        from refactron.core.metrics import get_metrics_collector

        console.print("\n[bold]Metrics Summary:[/bold]")
        collector = get_metrics_collector()
        metrics_summary = collector.get_analysis_summary()
        console.print(
            f"  Total analysis time: {metrics_summary.get('total_analysis_time_ms', 0):.2f}ms"
        )
        console.print(
            f"  Average time per file: {metrics_summary.get('average_time_per_file_ms', 0):.2f}ms"
        )
        console.print(f"  Success rate: {metrics_summary.get('success_rate_percent', 0):.1f}%")

    # Exit with error code: --fail-on sets threshold, default is CRITICAL
    _LEVEL_RANK = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 3}
    _SUMMARY_KEY = {
        "INFO": "info",
        "WARNING": "warnings",
        "ERROR": "errors",
        "CRITICAL": "critical",
    }

    effective_fail_on = fail_on.upper() if fail_on else "CRITICAL"
    threshold = _LEVEL_RANK[effective_fail_on]
    should_fail = any(
        summary[_SUMMARY_KEY[lvl]] > 0 for lvl, rank in _LEVEL_RANK.items() if rank >= threshold
    )
    if should_fail:
        raise SystemExit(1)


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
    help="Configuration profile to use (dev, staging, prod)",
)
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["dev", "staging", "prod"], case_sensitive=False),
    help="Environment to use (overrides profile)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    help="Report format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path",
)
def report(
    target: str,
    config: Optional[str],
    profile: Optional[str],
    environment: Optional[str],
    format: str,
    output: Optional[str],
) -> None:
    """
    Generate a detailed technical debt report.

    TARGET: Path to file or directory to analyze
    """
    console.print()
    _auth_banner("Report")
    console.print()

    target_path = Path(target)

    # Validate target
    if not target_path.exists():
        console.print(f"[error]Error: Path does not exist: {target}[/error]")
        raise SystemExit(1)

    cfg = _load_config(config, profile, environment)
    cfg.report_format = format

    console.print(f"[secondary]Format: {format.upper()}[/secondary]")

    try:
        with console.status("[primary]Analyzing code and generating report...[/primary]"):
            refactron = Refactron(cfg)
            result = refactron.analyze(target)

        report_content = result.report(detailed=True)

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            file_size = output_path.stat().st_size
            console.print(f"\nReport saved to: [bold]{output}[/bold]")
            console.print(f"[dim]Size: {file_size:,} bytes[/dim]")
        else:
            console.print(report_content)

    except Exception as e:
        console.print(f"[red]Report generation failed: {e}[/red]")
        raise SystemExit(1)


@click.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format",
)
def metrics(format: str) -> None:
    """
    Display collected metrics from the current session.

    Shows performance metrics, analyzer hit counts, and other statistics
    from Refactron operations.

    Examples:
      refactron metrics              # Show metrics in text format
      refactron metrics --format json  # Show metrics in JSON format
    """
    import json as json_module

    from refactron.core.metrics import get_metrics_collector

    console.print()
    _auth_banner("Metrics")
    console.print()

    collector = get_metrics_collector()
    summary = collector.get_combined_summary()

    if format == "json":
        console.print(json_module.dumps(summary, indent=2))
    else:
        # Text format
        analysis = summary.get("analysis", {})
        refactoring = summary.get("refactoring", {})

        # Analysis metrics
        console.print("[bold]Analysis Metrics:[/bold]")
        console.print(f"  Files analyzed: {analysis.get('total_files_analyzed', 0)}")
        console.print(f"  Files failed: {analysis.get('total_files_failed', 0)}")
        console.print(f"  Issues found: {analysis.get('total_issues_found', 0)}")
        console.print(f"  Total time: {analysis.get('total_analysis_time_ms', 0):.2f}ms")
        console.print(f"  Avg time per file: {analysis.get('average_time_per_file_ms', 0):.2f}ms")
        console.print(f"  Success rate: {analysis.get('success_rate_percent', 0):.1f}%")

        # Analyzer hit counts
        analyzer_hits = analysis.get("analyzer_hit_counts", {})
        if analyzer_hits:
            console.print("\n[bold]Analyzer Hit Counts:[/bold]")
            for analyzer, count in sorted(analyzer_hits.items()):
                console.print(f"  {analyzer}: {count}")

        # Refactoring metrics
        console.print("\n[bold]Refactoring Metrics:[/bold]")
        console.print(f"  Applied: {refactoring.get('total_refactorings_applied', 0)}")
        console.print(f"  Failed: {refactoring.get('total_refactorings_failed', 0)}")
        console.print(f"  Total time: {refactoring.get('total_refactoring_time_ms', 0):.2f}ms")
        console.print(f"  Success rate: {refactoring.get('success_rate_percent', 0):.1f}%")

        # Refactorer hit counts
        refactorer_hits = refactoring.get("refactorer_hit_counts", {})
        if refactorer_hits:
            console.print("\n[bold]Refactorer Hit Counts:[/bold]")
            for refactorer, count in sorted(refactorer_hits.items()):
                console.print(f"  {refactorer}: {count}")


@click.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind Prometheus metrics server to (default: 127.0.0.1 for localhost-only)",
)
@click.option(
    "--port",
    default=9090,
    type=int,
    help="Port for Prometheus metrics server",
)
def serve_metrics(host: str, port: int) -> None:
    """
    Start a Prometheus metrics HTTP server.

    This command starts a persistent HTTP server that exposes Refactron metrics
    in Prometheus format on the /metrics endpoint.

    Examples:
      refactron serve-metrics                    # Start on 0.0.0.0:9090
      refactron serve-metrics --port 8080        # Start on port 8080
      refactron serve-metrics --host 127.0.0.1   # Bind to localhost only
    """
    from refactron.core.prometheus_metrics import start_metrics_server

    console.print()
    _auth_banner("Metrics Server")
    console.print()

    try:
        start_metrics_server(host=host, port=port)
        console.print(f"[success]Metrics server started on http://{host}:{port}[/success]")
        console.print("\n[dim]Endpoints:[/dim]")
        console.print(f"[dim]  • http://{host}:{port}/metrics - Prometheus metrics[/dim]")
        console.print(f"[dim]  • http://{host}:{port}/health  - Health check[/dim]")
        console.print("\n[warning]Press Ctrl+C to stop the server[/warning]")

        # Keep the server running
        try:
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n\n[warning]Stopping metrics server...[/warning]")
            from refactron.core.prometheus_metrics import stop_metrics_server

            stop_metrics_server()
            console.print("[success]Metrics server stopped[/success]")
    except Exception as e:
        console.print(f"[red]Failed to start metrics server: {e}[/red]")
        raise SystemExit(1)


@click.command()
@click.argument("target", required=False, type=click.Path(exists=True))
@click.option("--line", type=int, help="Specific line number to fix")
@click.option("--interactive/--no-interactive", default=True, help="Use interactive mode")
@click.option(
    "--apply/--no-apply",
    default=False,
    help="Apply the suggested changes to the file",
)
def suggest(target: Optional[str], line: Optional[int], interactive: bool, apply: bool) -> None:
    """
    Generate AI-powered refactoring suggestions.

    Uses RAG and LLM to analyze code and propose fixes.
    """
    from rich.markdown import Markdown

    from refactron.core.backup import BackupRollbackSystem

    console.print()
    _auth_banner("AI Refactoring")
    console.print()

    # 1. Setup
    cfg = _load_config(None)
    _setup_logging()

    target_path = Path(target or ".").resolve()

    # Try to find the project root for RAG context
    refactron_instance = Refactron(cfg)
    workspace_path = refactron_instance.detect_project_root(target_path)

    console.print(f"[bold]Analyzing:[/bold] {target_path}")
    if line:
        console.print(f"[bold]Line:[/bold] {line}")

    # 2. Initialize Components
    try:
        retriever = ContextRetriever(workspace_path)
        console.print("[dim]RAG Index loaded.[/dim]")
    except Exception:
        console.print(
            "[yellow]Warning: RAG index not found. Context retrieval will be limited.[/yellow]"
        )
        console.print("[dim]Run 'refactron rag index' to enable full context.[/dim]")
        retriever = None

    orchestrator = LLMOrchestrator(retriever=retriever)

    # 3. Read Code
    start_line_idx = 0
    end_line_idx = 0

    if target_path.is_file():
        code = target_path.read_text(encoding="utf-8")
        original_snippet = code
        # Extract snippet if line provided
        if line:
            lines = code.splitlines()
            if 1 <= line <= len(lines):
                # Context window +/- 10 lines for the LLM prompt
                start_line_idx = max(0, line - 10)
                end_line_idx = min(len(lines), line + 10)
                original_snippet = "\n".join(lines[start_line_idx:end_line_idx])

                # Smaller context for display
                display_start = max(0, line - 3)
                display_end = min(len(lines), line + 3)
                display_code = "\n".join(lines[display_start:display_end])
                console.print(Panel(display_code, title="Code Snippet", style="dim"))
            else:
                console.print(f"[red]Error: Line {line} is out of range.[/red]")
                return
    else:
        console.print(
            "[red]Error: Directory analysis not yet supported. Please specify a file.[/red]"
        )
        return

    # 4. Generate Suggestion
    # Create a synthetic issue for now
    issue = CodeIssue(
        category=IssueCategory.MODERNIZATION,
        level=IssueLevel.INFO,
        message="Refactor and improve this code",
        file_path=target_path,
        line_number=line or 1,
    )

    with console.status("[bold cyan]Generating suggestion...[/bold cyan]"):
        suggestion = orchestrator.generate_suggestion(issue, original_code=original_snippet)

    # 5. Display Result
    if suggestion.status == SuggestionStatus.FAILED:
        console.print(f"[red]Generation Failed:[/red] {suggestion.explanation}")
        return

    console.print()
    console.print(
        Panel(
            Markdown(suggestion.explanation),
            title=f"Suggestion ({suggestion.model_name})",
            border_style="green",
        )
    )

    console.print(Panel(suggestion.proposed_code, title="Proposed Code", style="on #1e1e1e"))

    console.print(
        f"[dim]AI Confidence: [bold]{suggestion.llm_confidence:.2f}[/bold], Safety Score: [bold]{suggestion.confidence_score:.2f}[/bold][/dim]"  # noqa: E501
    )

    if suggestion.safety_result:
        status_color = "green" if suggestion.safety_result.passed else "red"
        console.print(
            f"Safety Check: [{status_color}]{'PASSED' if suggestion.safety_result.passed else 'FAILED'}[/{status_color}]"  # noqa: E501
        )
        if suggestion.safety_result.issues:
            console.print(f"Issues: {', '.join(suggestion.safety_result.issues)}")

    console.print()

    # 6. Apply Changes
    if apply:
        if interactive:
            if not click.confirm("Do you want to apply these changes?"):
                console.print("[yellow]Changes cancelled.[/yellow]")
                return

        try:
            # Create backup
            backup_sys = BackupRollbackSystem(workspace_path)
            session_id, _ = backup_sys.prepare_for_refactoring(
                [target_path], description="AI suggestion"
            )
            console.print(f"[dim]Backup created: {session_id}[/dim]")

            # Construct new content
            new_file_content = ""
            if line:
                # Reload lines to ensure freshness
                current_lines = target_path.read_text(encoding="utf-8").splitlines()
                # Determine indentation of the original block to verify alignment (optional, skipping for now)  # noqa: E501

                # Replace the exact block that was sent to LLM
                replacement_lines = suggestion.proposed_code.splitlines()

                # Reconstruct
                pre_block = current_lines[:start_line_idx]
                post_block = current_lines[end_line_idx:]

                final_lines = pre_block + replacement_lines + post_block
                new_file_content = "\n".join(final_lines)
                if code.endswith("\n"):
                    new_file_content += "\n"
            else:
                new_file_content = suggestion.proposed_code

            target_path.write_text(new_file_content, encoding="utf-8")
            console.print("[green bold]Successfully applied AI suggestion![/green bold]")
            console.print(f"[dim]Run 'refactron rollback {session_id}' to undo.[/dim]")

        except Exception as e:
            console.print(f"[red]Failed to apply changes: {e}[/red]")
