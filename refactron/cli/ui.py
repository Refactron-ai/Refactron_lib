"""
Shared UI components for the Refactron CLI.
Contains the Rich theme, console instance, and common display functions.
"""

import platform
import random
import sys
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, List, Optional, Set, Tuple

import click
from rich import box
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from refactron import __version__
from refactron.core.analysis_result import AnalysisResult
from refactron.core.models import IssueLevel
from refactron.core.refactor_result import RefactorResult

if TYPE_CHECKING:
    from refactron import Refactron

# Custom theme for a premium, modern look
THEME = Theme(
    {
        "primary": "bold #5f5fff",  # A vibrant indigo/blue
        "secondary": "#8a8a8a",  # Sleek gray
        "success": "bold #00d787",  # Modern mint/green
        "warning": "bold #ffaf00",  # Warm amber
        "error": "bold #ff5f5f",  # Soft red
        "info": "#5fafff",  # Sky blue
        "highlight": "bold #ffffff",  # Bright white
        "link": "underline #5f5fff",  # Link color
        "panel.border": "#444444",  # Subtle border
    }
)

console = Console(theme=THEME)


def _auth_banner(title: str) -> None:
    """Display a premium, stylized banner."""
    # Create a modern header with a tagline
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)

    # Title with gradient-like effect (simulated with colors)
    header_text = Text()
    header_text.append("Refactron", style="primary")
    header_text.append(" | ", style="secondary")
    header_text.append(title, style="highlight")

    grid.add_row(header_text)
    grid.add_row(
        Text(
            "The Intelligent Code Refactoring Transformer",
            style="secondary italic",
        )
    )

    console.print(
        Panel(
            grid,
            style="panel.border",
            box=box.ROUNDED,
            padding=(1, 2),
            subtitle=f"[secondary]v{__version__}[/secondary]",
            subtitle_align="right",
        )
    )


def _print_file_count(target_path: Any) -> None:
    """Print count of Python files if target is directory."""
    # Note: target_path typed as Any to avoid circular imports or Path issues
    if target_path.is_dir():
        py_files = list(target_path.rglob("*.py"))
        console.print(f"[dim]Found {len(py_files)} Python file(s) to analyze[/dim]\n")


def _create_summary_table(summary: dict) -> Table:
    """Create analysis summary table."""
    table = Table(
        title="Analysis Summary",
        show_header=True,
        header_style="primary",
        box=box.ROUNDED,
        border_style="panel.border",
        expand=True,
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold white")

    table.add_row("Files Found", str(summary["total_files"]))
    table.add_row("Files Analyzed", str(summary["files_analyzed"]))
    if summary.get("files_failed", 0) > 0:
        table.add_row("Files Failed", str(summary["files_failed"]), style="bold red")

    table.add_row(
        "Total Issues",
        str(summary["total_issues"]),
        style="bold yellow" if summary["total_issues"] > 0 else "bold green",
    )

    if summary["critical"] > 0:
        table.add_row("Critical", str(summary["critical"]), style="bold red")
    else:
        table.add_row("Critical", "0", style="dim")

    table.add_row(
        "Errors",
        str(summary["errors"]),
        style="bold red" if summary["errors"] > 0 else "dim",
    )
    table.add_row(
        "Warnings",
        str(summary["warnings"]),
        style="bold yellow" if summary["warnings"] > 0 else "dim",
    )
    table.add_row(
        "Info",
        str(summary["info"]),
        style="cyan" if summary["info"] > 0 else "dim",
    )

    return table


def _print_status_messages(summary: dict) -> None:
    """Print status messages based on analysis results."""
    if summary.get("files_failed", 0) > 0:
        console.print(
            f"[warning]{summary['files_failed']} file(s) failed analysis "
            f"and were skipped[/warning]"
        )

    if summary["total_issues"] == 0 and summary.get("files_failed", 0) == 0:
        console.print(
            Panel(
                "[success]Excellent! No issues found.[/success]",
                box=box.ROUNDED,
                border_style="success",
            )
        )
    elif summary["total_issues"] == 0 and summary.get("files_failed", 0) > 0:
        console.print(
            "[warning]No issues found in analyzed files, but some files failed.[/warning]"
        )
    elif summary["critical"] > 0:
        console.print(
            f"[error]Found {summary['critical']} critical issue(s) that need immediate "
            f"attention![/error]"
        )


def _relative_path(file_path: Any) -> str:
    """Convert an absolute path to a relative one (from cwd), or just the filename."""
    from pathlib import Path as _Path

    try:
        return str(_Path(file_path).relative_to(_Path.cwd()))
    except ValueError:
        return _Path(file_path).name


def _severity_style(level_name: str) -> str:
    """Map severity name to a Rich style string."""
    return {
        "critical": "bold red",
        "error": "red",
        "warning": "bold yellow",
        "info": "cyan",
    }.get(level_name, "dim")


_SEVERITY_ORDER = [
    ("critical", IssueLevel.CRITICAL),
    ("error", IssueLevel.ERROR),
    ("warning", IssueLevel.WARNING),
    ("info", IssueLevel.INFO),
]

# ─── Key constants ───────────────────────────────────────────────────

KEY_UP = "\x1b[A"
KEY_DOWN = "\x1b[B"
KEY_ENTER = "\r"

# Type alias: list of (level_name, issues_list) tuples
TuiGroups = List[Tuple[str, list]]


@dataclass
class TuiState:
    """Immutable-ish state for the TUI issue viewer."""

    groups: TuiGroups
    screen: str = "summary"  # "summary" or "group"
    cursor: int = 0
    current_group: int = 0
    expanded: Set[Tuple[int, int]] = field(default_factory=set)
    quit: bool = False


def _build_tui_groups(result: AnalysisResult) -> TuiGroups:
    """Build ordered list of (level_name, issues) for non-empty severity groups."""
    groups: TuiGroups = []
    for name, level in _SEVERITY_ORDER:
        issues = result.issues_by_level(level)
        if issues:
            groups.append((name, issues))
    return groups


def _handle_key(state: TuiState, key: str) -> TuiState:
    """Pure state transition: given current state + key, return new state."""
    if key == "q":
        return TuiState(
            groups=state.groups,
            screen=state.screen,
            cursor=state.cursor,
            current_group=state.current_group,
            expanded=state.expanded,
            quit=True,
        )

    if state.screen == "summary":
        return _handle_summary_key(state, key)
    elif state.screen == "group":
        return _handle_group_key(state, key)

    return state


def _handle_summary_key(state: TuiState, key: str) -> TuiState:
    """Handle key press on the summary screen."""
    max_idx = len(state.groups) - 1

    if key == KEY_DOWN:
        new_cursor = min(state.cursor + 1, max_idx)
        return TuiState(
            groups=state.groups,
            screen="summary",
            cursor=new_cursor,
            current_group=state.current_group,
            expanded=state.expanded,
        )
    elif key == KEY_UP:
        new_cursor = max(state.cursor - 1, 0)
        return TuiState(
            groups=state.groups,
            screen="summary",
            cursor=new_cursor,
            current_group=state.current_group,
            expanded=state.expanded,
        )
    elif key == KEY_ENTER:
        return TuiState(
            groups=state.groups,
            screen="group",
            cursor=0,
            current_group=state.cursor,
            expanded=state.expanded,
        )

    return state


def _handle_group_key(state: TuiState, key: str) -> TuiState:
    """Handle key press on a group detail screen."""
    _, issues = state.groups[state.current_group]
    max_idx = len(issues) - 1

    if key == KEY_DOWN:
        new_cursor = min(state.cursor + 1, max_idx)
        return TuiState(
            groups=state.groups,
            screen="group",
            cursor=new_cursor,
            current_group=state.current_group,
            expanded=state.expanded,
        )
    elif key == KEY_UP:
        new_cursor = max(state.cursor - 1, 0)
        return TuiState(
            groups=state.groups,
            screen="group",
            cursor=new_cursor,
            current_group=state.current_group,
            expanded=state.expanded,
        )
    elif key == KEY_ENTER:
        toggle_key = (state.current_group, state.cursor)
        new_expanded = set(state.expanded)
        if toggle_key in new_expanded:
            new_expanded.discard(toggle_key)
        else:
            new_expanded.add(toggle_key)
        return TuiState(
            groups=state.groups,
            screen="group",
            cursor=state.cursor,
            current_group=state.current_group,
            expanded=new_expanded,
        )
    elif key == "b":
        return TuiState(
            groups=state.groups,
            screen="summary",
            cursor=state.current_group,
            current_group=state.current_group,
            expanded=state.expanded,
        )
    elif key == "n":
        if state.current_group < len(state.groups) - 1:
            return TuiState(
                groups=state.groups,
                screen="group",
                cursor=0,
                current_group=state.current_group + 1,
                expanded=state.expanded,
            )
        return state
    elif key == "p":
        if state.current_group > 0:
            return TuiState(
                groups=state.groups,
                screen="group",
                cursor=0,
                current_group=state.current_group - 1,
                expanded=state.expanded,
            )
        return state

    return state


def _read_key() -> str:
    """Read a single keypress from stdin, handling escape sequences for arrow keys."""
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                return "\x1b[" + ch3
            return ch + ch2
        if ch == "\n":
            return KEY_ENTER
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _render_tui_summary(state: TuiState, target_path: Any) -> Text:
    """Render the summary screen as a Rich Text object."""
    from pathlib import Path as _Path

    target = _Path(target_path)
    label = target.name if target.is_file() else str(_relative_path(target))

    total = sum(len(issues) for _, issues in state.groups)

    output = Text()
    output.append(f"\n  {total} issues", style="bold")
    output.append(" found in ", style="")
    output.append(f"{label}\n\n", style="bold")

    for idx, (level_name, issues) in enumerate(state.groups):
        style = _severity_style(level_name)
        is_selected = idx == state.cursor
        prefix = "  > " if is_selected else "    "
        row_style = "bold " + style if is_selected else style

        count = len(issues)
        suffix = ""
        if level_name == "critical" and count > 0:
            suffix = "  <-- needs attention"

        line = f"{prefix}{level_name.upper():<12} {count:>4}{suffix}\n"
        output.append(line, style=row_style)

    output.append("\n  ")
    output.append("↑↓", style="bold")
    output.append(" Navigate   ", style="dim")
    output.append("Enter", style="bold")
    output.append(" Select   ", style="dim")
    output.append("q", style="bold")
    output.append(" Quit\n", style="dim")
    return output


def _render_tui_group(state: TuiState) -> Text:
    """Render a severity group detail screen as a Rich Text object."""
    level_name, issues = state.groups[state.current_group]
    style = _severity_style(level_name)

    output = Text()
    output.append(f"\n  ── {level_name.upper()} ({len(issues)}) ", style=style)
    output.append("─" * 40 + "\n\n", style="dim")

    for idx, issue in enumerate(issues):
        is_selected = idx == state.cursor
        is_expanded = (state.current_group, idx) in state.expanded
        prefix = "  > " if is_selected else "    "
        rel = _relative_path(issue.file_path)

        # Issue line
        issue_style = "bold " + style if is_selected else style
        output.append(f"{prefix}{rel}:{issue.line_number}", style=issue_style)
        output.append(f"  {issue.message}\n", style="")

        if is_expanded:
            snippet = _read_code_context(issue.file_path, issue.line_number, context=1)
            if snippet:
                for line_no, line_text in snippet:
                    marker = ">" if line_no == issue.line_number else " "
                    output.append(f"      {marker} {line_no:>4}| {line_text}\n", style="dim")
            if issue.suggestion:
                output.append(f"      Tip: {issue.suggestion}\n", style="dim")
            output.append("\n")

    # Navigation bar
    output.append("\n  ")
    output.append("↑↓", style="bold")
    output.append(" Navigate   ", style="dim")
    output.append("Enter", style="bold")
    output.append(" Expand/Collapse   ", style="dim")
    output.append("b", style="bold")
    output.append(" Back   ", style="dim")
    if state.current_group < len(state.groups) - 1:
        next_name = state.groups[state.current_group + 1][0].upper()
        output.append("n", style="bold")
        output.append(f" Next ({next_name})   ", style="dim")
    if state.current_group > 0:
        prev_name = state.groups[state.current_group - 1][0].upper()
        output.append("p", style="bold")
        output.append(f" Prev ({prev_name})   ", style="dim")
    output.append("q", style="bold")
    output.append(" Quit\n", style="dim")

    return output


def _read_code_context(file_path: Any, line_number: int, context: int = 1) -> Optional[list]:
    """Read a few lines around *line_number* from the source file.

    Returns a list of ``(lineno, text)`` tuples, or ``None`` on failure.
    """
    from pathlib import Path as _Path

    try:
        lines = _Path(file_path).read_text(encoding="utf-8").splitlines()
        start = max(0, line_number - 1 - context)
        end = min(len(lines), line_number + context)
        return [(i + 1, lines[i]) for i in range(start, end)]
    except Exception:
        return None


def _print_single_issue(issue: Any, show_code: bool = False) -> None:
    """Print one issue with optional code context."""
    rel = _relative_path(issue.file_path)
    style = _severity_style(issue.level.value)

    console.print(f"  [{style}]{rel}:{issue.line_number}[/{style}]  {issue.message}")

    if show_code:
        snippet = _read_code_context(issue.file_path, issue.line_number, context=1)
        if snippet:
            for line_no, line_text in snippet:
                marker = ">" if line_no == issue.line_number else " "
                console.print(f"  [dim]  {marker} {line_no:>4}[/dim]| {line_text}")

    if issue.suggestion:
        console.print(f"  [dim]  Tip: {issue.suggestion}[/dim]")

    console.print()


def _print_severity_group(level_name: str, issues: list) -> None:
    """Print all issues for one severity group."""
    style = _severity_style(level_name)
    show_code = level_name in ("critical", "error", "warning")

    console.print()
    console.print(Rule(f" {level_name.upper()} ({len(issues)}) ", style=style))
    console.print()

    for issue in issues:
        _print_single_issue(issue, show_code=show_code)


def _group_issues(result: AnalysisResult) -> dict:
    """Group issues by severity level. Returns {name: [issues]} for non-empty groups."""
    groups: dict = {}
    for name, level in _SEVERITY_ORDER:
        issues = result.issues_by_level(level)
        if issues:
            groups[name] = issues
    return groups


# ─── Non-interactive output (CI/CD, piped) ────────────────────────────────


def _print_detailed_issues(result: AnalysisResult) -> None:
    """Print issues grouped by severity (non-interactive mode)."""
    groups = _group_issues(result)
    if not groups:
        return

    for level_name in ["critical", "error", "warning", "info"]:
        if level_name in groups:
            _print_severity_group(level_name, groups[level_name])


def _print_helpful_tips(summary: dict, detailed: bool) -> None:
    """Print helpful tips based on results."""
    if summary["total_issues"] > 0 and not detailed:
        console.print("[secondary]Tip: Use --detailed to see all issues[/secondary]")

    if summary["total_issues"] > 5:
        console.print(
            "[secondary]Tip: Run 'refactron autofix <target> --dry-run'"
            " to preview fixes[/secondary]"
        )


# ─── Interactive viewer ───────────────────────────────────────────────────


def _erase_lines(n: int) -> None:
    """Move cursor up *n* lines and clear everything below."""
    if n > 0:
        sys.stdout.write(f"\x1b[{n}A\x1b[J")
        sys.stdout.flush()


def _interactive_issue_viewer(result: AnalysisResult, target_path: Any) -> None:
    """Interactive TUI issue browser with arrow key navigation (TTY only).

    Uses termios raw mode for key capture and manual cursor erasure for
    flicker-free re-rendering.  Arrow keys navigate, Enter expands/collapses,
    q quits.
    """
    groups = _build_tui_groups(result)

    if not groups:
        console.print(
            Panel(
                "[success]Excellent! No issues found.[/success]",
                box=box.ROUNDED,
                border_style="success",
            )
        )
        return

    state = TuiState(groups=groups)
    last_height = 0

    try:
        while not state.quit:
            # Erase previous frame
            _erase_lines(last_height)

            # Build renderable
            if state.screen == "summary":
                renderable = _render_tui_summary(state, target_path)
            else:
                renderable = _render_tui_group(state)

            # Capture to count lines, then write to terminal
            with console.capture() as cap:
                console.print(renderable, highlight=False)
            output = cap.get()
            last_height = output.count("\n")
            sys.stdout.write(output)
            sys.stdout.flush()

            # Wait for keypress
            key = _read_key()
            state = _handle_key(state, key)

        # Erase the TUI on quit, leave a clean summary
        _erase_lines(last_height)
        total = sum(len(iss) for _, iss in groups)
        console.print(f"  [dim]{total} issues found. Done.[/dim]")
    except (KeyboardInterrupt, EOFError):
        _erase_lines(last_height)


def _print_refactor_filters(types: tuple) -> None:
    """Print operation type filters if specified."""
    if types:
        console.print(f"[secondary]Filtering for: {', '.join(types)}[/secondary]\n")


def _confirm_apply_mode(preview: bool) -> None:
    """Warn and confirm if using --apply mode."""
    if not preview:
        console.print("[warning]--apply mode will modify your files![/warning]")
        if not click.confirm("Continue?"):
            raise SystemExit(0)


def _create_refactor_table(summary: dict) -> Table:
    """Create refactoring summary table."""
    table = Table(
        title="Refactoring Summary",
        show_header=True,
        header_style="primary",
        box=box.ROUNDED,
        border_style="panel.border",
        expand=True,
    )
    table.add_column("Metric", style="info")
    table.add_column("Value", justify="right", style="highlight")

    table.add_row("Total Operations", str(summary["total_operations"]))
    table.add_row("Safe Operations", str(summary["safe"]), style="success")

    if summary["high_risk"] > 0:
        table.add_row("High Risk", str(summary["high_risk"]), style="error bold")
    else:
        table.add_row("High Risk", "0", style="secondary")

    table.add_row("Applied", "Yes" if summary["applied"] else "No", style="highlight")

    return table


def _print_refactor_messages(summary: dict, preview: bool) -> None:
    """Print status messages for refactoring results."""
    if summary["total_operations"] == 0:
        console.print(
            Panel(
                "[success]No refactoring opportunities found. Your code looks good![/success]",
                box=box.ROUNDED,
                border_style="success",
            )
        )
    elif summary["high_risk"] > 0:
        console.print(
            f"[warning]{summary['high_risk']} operation(s) are high-risk. Review "
            f"carefully![/warning]"
        )

    if preview and summary["total_operations"] > 0:
        console.print("\n[info]This is a preview. Use --apply to apply changes.[/info]")
        console.print("[secondary]Tip: Review each change carefully before applying[/secondary]")

    if summary["total_operations"] > 0 and summary["applied"]:
        console.print("\n[success]Refactoring completed! Don't forget to test your code.[/success]")


def _collect_feedback_interactive(refactron: "Refactron", result: RefactorResult) -> None:
    """
    Collect feedback from user interactively for each refactoring operation.

    Args:
        refactron: Refactron instance to record feedback
        result: RefactorResult containing operations
    """
    if not result.operations:
        return

    console.print("\n[bold]Feedback Collection (Optional)[/bold]")
    console.print("[dim]Help us learn from your feedback to improve suggestions![/dim]\n")

    for op in result.operations:
        console.print(f"\n[cyan]Operation ID: {op.operation_id}[/cyan]")
        console.print(f"[dim]Type: {op.operation_type} at {op.file_path}:{op.line_number}[/dim]")
        ranking_score = result.get_ranking_score(op)
        if ranking_score > 0:
            console.print(f"[dim]Ranking Score: {ranking_score:.3f}[/dim]")

        action = click.prompt(
            "Your feedback? (a)ccepted, (r)ejected, (i)gnored, or (s)kip",
            type=click.Choice(["a", "r", "i", "s"], case_sensitive=False),
            default="s",
        ).lower()

        if action == "s":
            continue

        reason = None
        if action in ("r", "a", "i"):
            reason = click.prompt(
                "Reason (optional, press Enter to skip)",
                default="",
                show_default=False,
            )
            if not reason.strip():
                reason = None

        action_map = {"a": "accepted", "r": "rejected", "i": "ignored"}
        refactron.record_feedback(
            operation_id=op.operation_id,
            action=action_map[action],
            reason=reason,
            operation=op,
        )

    console.print("\n[success]Thank you for your feedback![/success]")


def _record_applied_operations(refactron: "Refactron", result: RefactorResult) -> None:
    """
    Automatically record all operations as accepted when --apply is used.

    Args:
        refactron: Refactron instance to record feedback
        result: RefactorResult containing operations
    """
    if not result.operations:
        return

    for op in result.operations:
        refactron.record_feedback(
            operation_id=op.operation_id,
            action="accepted",
            reason="Applied via --apply flag",
            operation=op,
        )


def _run_startup_animation() -> None:
    """Run a sleek startup animation with a big logo and system info."""
    # Clear screen first
    console.clear()

    LOGO_LINES = [
        r"██████╗ ███████╗███████╗ █████╗  ██████╗████████╗██████╗  ██████╗ ███╗   ██╗",
        r"██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗████╗  ██║",
        r"██████╔╝█████╗  █████╗  ███████║██║        ██║   ██████╔╝██║   ██║██╔██╗ ██║",
        r"██╔══██╗██╔══╝  ██╔══╝  ██╔══██║██║        ██║   ██╔══██╗██║   ██║██║╚██╗██║",
        r"██║  ██║███████╗██║     ██║  ██║╚██████╗   ██║   ██║  ██║╚██████╔╝██║ ╚████║",
        r"╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝",
    ]

    subtitle_text = "The Intelligent Code Refactoring Transformer"

    TIPS = [
        "Tip: Use 'refactron analyze' to find technical debt.",
        "Tip: 'refactron rollback' can undo your last changes.",
        "Tip: Check '.refactron.yaml' to customize behavior.",
        "Tip: Run 'refactron serve-metrics' for Prometheus data.",
        "Tip: Use --detailed for a deeper analysis report.",
    ]

    CHECKS = [
        "Verifying configuration...",
        "Checking credentials...",
        "Initializing refactoring engine...",
        "Scanning project structure...",
        "Ready to transform.",
    ]

    selected_tip = random.choice(TIPS)

    def get_renderable(step: int, phase: str) -> Align:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(Text("\n" * 2))  # Top padding

        if phase == "check":
            # System check phase
            check_idx = min(step // 5, len(CHECKS) - 1)
            grid.add_row(Align.center(Text("SYSTEM CHECK", style="bold #5f5fff")))
            grid.add_row(Align.center(Text(CHECKS[check_idx], style="dim")))

            # Mini progress bar
            width = 30
            filled = int((step / 25) * width)
            bar = "━" * filled + " " * (width - filled)
            grid.add_row(Align.center(Text(f"[{bar}]", style="#5f5fff")))

        elif phase == "logo":
            # Reveal logo wipe
            max_len = max(len(line) for line in LOGO_LINES)
            reveal_len = int((step / 30) * max_len)

            logo_text = Text()
            for line in LOGO_LINES:
                visible_part = line[:reveal_len]
                logo_text.append(visible_part + "\n", style="bold #ffffff")

            grid.add_row(Align.center(logo_text))

        elif phase == "final":
            # Logo static
            logo_text = Text()
            for line in LOGO_LINES:
                logo_text.append(line + "\n", style="bold #ffffff")
            grid.add_row(Align.center(logo_text))

            # Subtitle
            grid.add_row(Align.center(Text(subtitle_text, style="italic #8a8a8a")))

            # System Info
            info_table = Table.grid(padding=(0, 2))
            info_table.add_column(style="dim", justify="right")
            info_table.add_column(style="bold white")

            info_table.add_row("Version:", f"v{__version__}")
            info_table.add_row("Python:", sys.version.split()[0])
            info_table.add_row("OS:", platform.system())

            grid.add_row(Text("\n"))
            grid.add_row(Align.center(info_table))

            # Tip
            grid.add_row(Text("\n"))
            grid.add_row(
                Align.center(
                    Panel(
                        Text(selected_tip, style="cyan"),
                        border_style="#333333",
                        expand=False,
                    )
                )
            )

        return Align.center(grid)

    with Live(console=console, refresh_per_second=20, transient=True) as live:
        # Phase 1: System Checks
        for i in range(26):
            live.update(get_renderable(i, "check"))
            time.sleep(0.04)

        # Phase 2: Logo Wipe
        for i in range(31):
            live.update(get_renderable(i, "logo"))
            time.sleep(0.03)

        # Phase 3: Final Reveal
        live.update(get_renderable(0, "final"))
        time.sleep(1.5)

    # Final static print
    console.print()
    for line in LOGO_LINES:
        console.print(Align.center(Text(line, style="bold #ffffff")))
    console.print(Align.center(Text(subtitle_text, style="italic #8a8a8a")))
    console.print(Align.center(Text(f"v{__version__}", style="dim")))
    console.print()


def _print_custom_help(ctx: click.Context) -> None:
    """Print a beautifully formatted, numbered help screen."""
    console.print()
    # Use a clean, bold header
    header = Table.grid(expand=True)
    header.add_column(justify="center")
    header.add_row(Text("⚡ REFACTRON", style="bold white"))
    header.add_row(Text("INTELLIGENT CODE REFACTORING", style="dim white"))
    console.print(Panel(header, border_style="#333333", padding=(1, 2)))

    console.print("\n[bold white]COMMAND CENTER[/bold white]")
    console.print("[dim]Select a command by name or number[/dim]\n")

    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.SIMPLE,
        expand=True,
        padding=(0, 2),
    )
    table.add_column("ID", justify="right", style="cyan", width=4)
    table.add_column("COMMAND", style="bold white", width=20)
    table.add_column("DESCRIPTION", style="dim")

    commands = sorted(ctx.command.list_commands(ctx))
    for i, cmd_name in enumerate(commands, 1):
        cmd = ctx.command.get_command(ctx, cmd_name)
        description = cmd.get_short_help_str() if cmd else ""
        table.add_row(f"{i:02d}", cmd_name.upper(), description)

    console.print(table)

    console.print("\n[bold cyan]GLOBAL OPTIONS[/bold cyan]")
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold white")
    grid.add_column(style="dim")
    grid.add_row("--version", "Show the version and exit.")
    grid.add_row("--help", "Show this message and exit.")
    console.print(grid)

    console.print("\n[dim]USAGE: refactron <command> [args]...[/dim]")
    console.print("[dim]EXAMPLE: refactron analyze . --detailed[/dim]\n")


def _run_minimal_loop(ctx: click.Context) -> None:
    """Run a minimal interactive loop for help and version only."""
    from refactron.core.credentials import load_credentials

    def print_header() -> None:
        creds = load_credentials()
        user = creds.email if creds else "Guest"
        plan = (creds.plan or "Free").upper() if creds else "N/A"

        # Profile Card Layout
        grid = Table.grid(expand=False, padding=(0, 3))
        grid.add_column(justify="center")
        grid.add_column(justify="left", vertical="middle")

        # Avatar (Simple ASCII)
        avatar = """
      ▄▄▄
     █████
    ███████
   █████████
  ███ █ █ ███
        """

        info = Table.grid(padding=(0, 1))
        info.add_column(style="dim", justify="right")
        info.add_column(style="bold white")

        info.add_row("User:", user)
        info.add_row("Plan:", plan)
        info.add_row("Status:", "[green]Online[/green]")

        grid.add_row(Text(avatar.strip(), style="#5f5fff"), info)

        console.print(
            Panel(
                grid,
                title="[bold]DASHBOARD[/bold]",
                border_style="#444444",
                box=box.ROUNDED,
                expand=False,
                padding=(1, 2),
            )
        )

    console.clear()
    print_header()

    while True:
        try:
            console.print("\n[bold]Available Options:[/bold]")
            console.print(
                "1. [bold blue]Help[/bold blue]      [dim]Show CLI usage and commands[/dim]"
            )
            console.print("2. [bold blue]Version[/bold blue]   [dim]Show current version[/dim]")
            console.print("3. [bold blue]Exit[/bold blue]")

            choice = Prompt.ask(
                "\n[bold]>[/bold] ",
                choices=["1", "2", "3"],
                default="3",
                show_choices=False,
            )

            if choice == "1":
                _print_custom_help(ctx)
            elif choice == "2":
                console.print(f"\nRefactron CLI v{__version__}")
            elif choice == "3":
                console.print("Goodbye!")
                break

        except KeyboardInterrupt:
            console.print("\nGoodbye!")
            break


def _interactive_file_selector(directory: Any, pattern: str = "*.py") -> Optional[Any]:
    """
    Interactively select a file from a directory.

    Args:
        directory: Path-like object
        pattern: Glob pattern to filter files

    Returns:
        Selected file Path or None if aborted/skipped
    """
    # Import locally to avoid circular dependencies
    from pathlib import Path

    target_dir = Path(directory)
    if not target_dir.exists():
        return None

    files = list(target_dir.rglob(pattern))
    if not files:
        console.print("[warning]No matching files found.[/warning]")
        return None

    # Limit to top 20 to avoid overwhelming UI
    display_files = files[:20]

    table = Table(title=f"Files in {target_dir.name}", box=box.SIMPLE)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Path", style="white")

    for i, path in enumerate(display_files, 1):
        rel_path = path.relative_to(target_dir)
        table.add_row(str(i), str(rel_path))

    console.print(table)
    if len(files) > 20:
        console.print(f"[dim]...and {len(files) - 20} more files[/dim]")

    choice = IntPrompt.ask("Select a file (0 to cancel)", default=0, show_default=True)

    if choice == 0 or choice > len(display_files):
        return None

    return display_files[choice - 1]
