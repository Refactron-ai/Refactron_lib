"""CLI output formatting for VerificationResult (Rich and JSON)."""

import json

from rich.console import Console

from refactron.verification.result import VerificationResult


def format_verification_result(result: VerificationResult, console: Console) -> None:
    """Print a VerificationResult to the console in a readable format."""
    if result.safe_to_apply:
        console.print()
        for cr in result.check_results:
            console.print(f"  [green]\u2713[/green] {cr.check_name} ({cr.duration_ms}ms)")
        for name, reason in result.skipped_checks:
            console.print(f"  [dim]- {name}: {reason}[/dim]")
        console.print(
            f"\n  [bold green]Safe to apply.[/bold green]"
            f" Confidence: {result.confidence_score:.1%}"
            f" | Total: {result.verification_ms}ms"
        )
    else:
        console.print()
        for cr in result.check_results:
            if cr.passed:
                console.print(f"  [green]\u2713[/green] {cr.check_name} ({cr.duration_ms}ms)")
            else:
                console.print(f"  [red]\u2717[/red] {cr.check_name} ({cr.duration_ms}ms)")
                console.print(f"      [red]{cr.blocking_reason}[/red]")
        for name, reason in result.skipped_checks:
            console.print(f"  [dim]- {name}: {reason}[/dim]")
        console.print(f"\n  [bold red]Blocked.[/bold red] {result.blocking_reason}")


def format_verification_result_json(result: VerificationResult, indent: int = 2) -> str:
    """Render a VerificationResult as a stable, machine-readable JSON string.

    Intended for CI gates, bots, and parent tools that need structured data
    rather than scraping terminal text. The schema is versioned — see
    ``VerificationResult.to_json_dict``.
    """
    return json.dumps(result.to_json_dict(), indent=indent, sort_keys=True)
