"""Command-line interface for Refactron."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from refactron import Refactron
from refactron.autofix.engine import AutoFixEngine
from refactron.autofix.models import FixRiskLevel
from refactron.core.config import RefactronConfig

console = Console()


def _load_config(config_path: Optional[str]) -> RefactronConfig:
    """Load configuration from file or use default."""
    try:
        if config_path:
            console.print(f"[dim]📄 Loading config from: {config_path}[/dim]")
            return RefactronConfig.from_file(Path(config_path))
        return RefactronConfig.default()
    except Exception as e:
        console.print(f"[red]❌ Error loading configuration: {e}[/red]")
        raise SystemExit(1)


def _validate_path(target: str) -> Path:
    """Validate target path exists."""
    target_path = Path(target)
    if not target_path.exists():
        console.print(f"[red]❌ Error: Path does not exist: {target}[/red]")
        raise SystemExit(1)
    return target_path


def _print_file_count(target_path: Path) -> None:
    """Print count of Python files if target is directory."""
    if target_path.is_dir():
        py_files = list(target_path.rglob("*.py"))
        console.print(f"[dim]📁 Found {len(py_files)} Python file(s) to analyze[/dim]\n")


def _create_summary_table(summary: dict) -> Table:
    """Create analysis summary table."""
    table = Table(title="Analysis Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("Files Analyzed", str(summary["total_files"]))
    table.add_row("Total Issues", str(summary["total_issues"]))
    table.add_row("🔴 Critical", str(summary["critical"]))
    table.add_row("❌ Errors", str(summary["errors"]))
    table.add_row("⚡ Warnings", str(summary["warnings"]))
    table.add_row("ℹ️  Info", str(summary["info"]))

    return table


def _print_status_messages(summary: dict) -> None:
    """Print status messages based on analysis results."""
    if summary["total_issues"] == 0:
        console.print("[green]✨ Excellent! No issues found.[/green]")
    elif summary["critical"] > 0:
        console.print(
            f"[red]⚠️  Found {summary['critical']} critical issue(s) that need immediate "
            f"attention![/red]"
        )


def _print_detailed_issues(result) -> None:
    """Print detailed issues list."""
    console.print("[bold]Detailed Issues:[/bold]\n")
    level_icons = {
        "critical": "🔴",
        "error": "❌",
        "warning": "⚡",
        "info": "ℹ️",
    }

    for issue in result.all_issues:
        icon = level_icons.get(issue.level.value, "•")
        console.print(f"{icon} {issue}")
        if issue.suggestion:
            console.print(f"   [dim]💡 {issue.suggestion}[/dim]")
        console.print()


def _print_helpful_tips(summary: dict, detailed: bool) -> None:
    """Print helpful tips based on results."""
    if summary["total_issues"] > 0 and not detailed:
        console.print("[dim]💡 Tip: Use --detailed to see all issues[/dim]")

    if summary["total_issues"] > 5:
        console.print(
            "[dim]💡 Tip: Run 'refactron refactor --preview' to see suggested fixes[/dim]"
        )


def _print_refactor_filters(types: tuple) -> None:
    """Print operation type filters if specified."""
    if types:
        console.print(f"[dim]🎯 Filtering for: {', '.join(types)}[/dim]\n")


def _confirm_apply_mode(preview: bool) -> None:
    """Warn and confirm if using --apply mode."""
    if not preview:
        console.print("[yellow]⚠️  --apply mode will modify your files![/yellow]")
        if not click.confirm("Continue?"):
            raise SystemExit(0)


def _create_refactor_table(summary: dict) -> Table:
    """Create refactoring summary table."""
    table = Table(title="Refactoring Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("Total Operations", str(summary["total_operations"]))
    table.add_row("Safe Operations", str(summary["safe"]))
    table.add_row("High Risk", str(summary["high_risk"]))
    table.add_row("Applied", "✅ Yes" if summary["applied"] else "❌ No")

    return table


def _print_refactor_messages(summary: dict, preview: bool) -> None:
    """Print status messages for refactoring results."""
    if summary["total_operations"] == 0:
        console.print("[green]✨ No refactoring opportunities found. Your code looks good![/green]")
    elif summary["high_risk"] > 0:
        console.print(
            f"[yellow]⚠️  {summary['high_risk']} operation(s) are high-risk. Review "
            f"carefully![/yellow]"
        )

    if preview and summary["total_operations"] > 0:
        console.print("\n[yellow]ℹ️  This is a preview. Use --apply to apply changes.[/yellow]")
        console.print("[dim]💡 Tip: Review each change carefully before applying[/dim]")

    if summary["total_operations"] > 0 and summary["applied"]:
        console.print("\n[green]✅ Refactoring completed! Don't forget to test your code.[/green]")


@click.group()
@click.version_option(version="1.0.0")
def main() -> None:
    """
    Refactron - The Intelligent Code Refactoring Transformer

    Analyze, refactor, and optimize your Python code with ease.
    """
    pass


@main.command()
@click.argument("target", type=click.Path(exists=True))
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
def analyze(target: str, config: Optional[str], detailed: bool) -> None:
    """
    Analyze code for issues and technical debt.

    TARGET: Path to file or directory to analyze
    """
    console.print("\n🔍 [bold blue]Refactron Analysis[/bold blue]\n")

    # Setup
    target_path = _validate_path(target)
    cfg = _load_config(config)
    _print_file_count(target_path)

    # Run analysis
    try:
        with console.status("[bold green]🔎 Analyzing code...[/bold green]"):
            refactron = Refactron(cfg)
            result = refactron.analyze(target)
    except Exception as e:
        console.print(f"[red]❌ Analysis failed: {e}[/red]")
        console.print("[dim]Tip: Check if all files have valid Python syntax[/dim]")
        raise SystemExit(1)

    # Display results
    summary = result.summary()
    console.print(_create_summary_table(summary))
    console.print()

    _print_status_messages(summary)

    if detailed and result.all_issues:
        _print_detailed_issues(result)

    _print_helpful_tips(summary, detailed)

    # Exit with error code if critical issues found
    if summary["critical"] > 0:
        raise SystemExit(1)


@main.command()
@click.argument("target", type=click.Path(exists=True))
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
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
def refactor(
    target: str,
    config: Optional[str],
    preview: bool,
    types: tuple,
) -> None:
    """
    Refactor code with intelligent transformations.

    TARGET: Path to file or directory to refactor
    """
    console.print("\n🔧 [bold blue]Refactron Refactoring[/bold blue]\n")

    # Setup
    _validate_path(target)
    cfg = _load_config(config)
    _print_refactor_filters(types)
    _confirm_apply_mode(preview)

    # Run refactoring
    try:
        with console.status("[bold green]🔎 Analyzing and generating refactorings...[/bold green]"):
            refactron = Refactron(cfg)
            result = refactron.refactor(
                target,
                preview=preview,
                operation_types=list(types) if types else None,
            )
    except Exception as e:
        console.print(f"[red]❌ Refactoring failed: {e}[/red]")
        raise SystemExit(1)

    # Display results
    summary = result.summary()
    console.print(_create_refactor_table(summary))
    console.print()

    _print_refactor_messages(summary, preview)

    if result.operations:
        console.print("[bold]Refactoring Operations:[/bold]\n")
        console.print(result.show_diff())


@main.command()
@click.argument("target", type=click.Path(exists=True))
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
def report(target: str, format: str, output: Optional[str]) -> None:
    """
    Generate a detailed technical debt report.

    TARGET: Path to file or directory to analyze
    """
    console.print("\n📊 [bold blue]Generating Report[/bold blue]\n")

    target_path = Path(target)

    # Validate target
    if not target_path.exists():
        console.print(f"[red]❌ Error: Path does not exist: {target}[/red]")
        raise SystemExit(1)

    cfg = RefactronConfig.default()
    cfg.report_format = format

    console.print(f"[dim]📝 Format: {format.upper()}[/dim]")

    try:
        with console.status("[bold green]📊 Analyzing code and generating report...[/bold green]"):
            refactron = Refactron(cfg)
            result = refactron.analyze(target)

        report_content = result.report(detailed=True)

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                f.write(report_content)

            file_size = output_path.stat().st_size
            console.print(f"\n✅ Report saved to: [bold]{output}[/bold]")
            console.print(f"[dim]📦 Size: {file_size:,} bytes[/dim]")
        else:
            console.print(report_content)

    except Exception as e:
        console.print(f"[red]❌ Report generation failed: {e}[/red]")
        raise SystemExit(1)


@main.command()
@click.argument("target", type=click.Path(exists=True))
@click.option(
    "--preview/--apply",
    default=True,
    help="Preview fixes or apply them",
)
@click.option(
    "--safety-level",
    "-s",
    type=click.Choice(["safe", "low", "moderate", "high"], case_sensitive=False),
    default="safe",
    help="Maximum risk level for automatic fixes",
)
def autofix(
    target: str,
    preview: bool,
    safety_level: str,
) -> None:
    """
    Automatically fix code issues (Phase 3 feature).

    TARGET: Path to file or directory to fix

    Examples:
      refactron autofix myfile.py --preview
      refactron autofix myproject/ --apply --safety-level moderate
    """
    console.print("\n🔧 [bold blue]Refactron Auto-fix[/bold blue]\n")

    # Setup
    target_path = _validate_path(target)
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

    if preview:
        console.print("[yellow]📋 Preview mode: No changes will be applied[/yellow]\n")
    else:
        console.print("[green]✅ Apply mode: Changes will be written to files[/green]\n")

    console.print(f"[dim]🛡️  Safety level: {safety_level}[/dim]")
    console.print(f"[dim]🔧 Available fixers: {len(engine.fixers)}[/dim]\n")

    # Display available fixers
    console.print("[bold]Available Auto-fixes:[/bold]\n")
    for fixer_name, fixer in engine.fixers.items():
        risk_emoji = "🟢" if fixer.risk_score == 0.0 else "🟡" if fixer.risk_score < 0.5 else "🔴"
        console.print(f"{risk_emoji} {fixer_name} (risk: {fixer.risk_score:.1f})")

    console.print(
        "\n[dim]💡 Tip: Auto-fix requires analyzed issues. Integration with analyzers "
        "coming soon![/dim]"
    )
    console.print(
        "[dim]📖 For now, use 'refactron analyze' to find issues, then 'refactron refactor' "
        "to fix them.[/dim]"
    )


@main.command()
def init() -> None:
    """Initialize Refactron configuration in the current directory."""
    config_path = Path(".refactron.yaml")

    if config_path.exists():
        console.print("[yellow]⚠️  Configuration file already exists![/yellow]")
        if not click.confirm("Overwrite?"):
            return

    cfg = RefactronConfig.default()
    cfg.to_file(config_path)

    console.print(f"✅ Created configuration file: {config_path}")
    console.print("\n[dim]Edit this file to customize Refactron behavior.[/dim]")


@main.group()
def ai() -> None:
    """AI-powered code analysis and suggestions (optional features)."""
    pass


@ai.command("explain")
@click.argument("target", type=click.Path(exists=True))
@click.option("--provider", type=click.Choice(["openai", "anthropic", "ollama"]), default="openai")
@click.option("--api-key", help="API key (not needed for Ollama)")
@click.option("--model", help="Model name (optional)")
def ai_explain(target: str, provider: str, api_key: Optional[str], model: Optional[str]) -> None:
    """Get AI explanation of code."""
    from refactron.ai import create_ai_service

    try:
        console.print(f"[cyan]🤖 Analyzing {target} with AI ({provider})...[/cyan]\n")

        # Create AI service
        ai_service = create_ai_service(provider=provider, api_key=api_key, model=model)

        # Read code
        with open(target, "r") as f:
            code = f.read()

        # Get explanation
        explanation = ai_service.explain_code(code)

        console.print("[bold green]📖 Code Explanation:[/bold green]")
        console.print(explanation)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        console.print("\n[dim]💡 Tips:[/dim]")
        console.print("[dim]- For OpenAI: Set OPENAI_API_KEY environment variable[/dim]")
        console.print("[dim]- For Anthropic: Set ANTHROPIC_API_KEY environment variable[/dim]")
        console.print("[dim]- For Ollama: Install from https://ollama.ai[/dim]")
        raise SystemExit(1)


@ai.command("suggest")
@click.argument("target", type=click.Path(exists=True))
@click.option("--provider", type=click.Choice(["openai", "anthropic", "ollama"]), default="openai")
@click.option("--api-key", help="API key (not needed for Ollama)")
@click.option("--model", help="Model name (optional)")
def ai_suggest(target: str, provider: str, api_key: Optional[str], model: Optional[str]) -> None:
    """Get AI-powered improvement suggestions."""
    from refactron.ai import AIConfig, AIProvider

    try:
        console.print(f"[cyan]🤖 Getting AI suggestions for {target}...[/cyan]\n")

        # Create AI config
        ai_config = AIConfig(
            enabled=True,
            provider=AIProvider(provider),
            api_key=api_key,
            model=model,
        )

        # Create Refactron with AI
        refactron = Refactron(ai_config=ai_config)

        # Get suggestions
        suggestions = refactron.get_ai_suggestions(target)

        console.print("[bold green]📖 Code Explanation:[/bold green]")
        console.print(suggestions["explanation"])
        console.print("\n[bold yellow]💡 Improvement Suggestions:[/bold yellow]")
        console.print(suggestions["improvements"])
        console.print("\n[bold cyan]⚡ Optimization Recommendations:[/bold cyan]")
        console.print(suggestions["optimizations"])

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        console.print("\n[dim]💡 Tips:[/dim]")
        console.print("[dim]- For OpenAI: Set OPENAI_API_KEY environment variable[/dim]")
        console.print("[dim]- For Anthropic: Set ANTHROPIC_API_KEY environment variable[/dim]")
        console.print("[dim]- For Ollama: Install from https://ollama.ai[/dim]")
        raise SystemExit(1)


@ai.command("document")
@click.argument("target", type=click.Path(exists=True))
@click.option("--provider", type=click.Choice(["openai", "anthropic", "ollama"]), default="openai")
@click.option("--api-key", help="API key (not needed for Ollama)")
@click.option("--model", help="Model name (optional)")
@click.option("--function", help="Specific function to document")
def ai_document(
    target: str,
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    function: Optional[str],
) -> None:
    """Generate AI-powered documentation."""
    from refactron.ai import AIConfig, AIProvider

    try:
        console.print(f"[cyan]🤖 Generating documentation for {target}...[/cyan]\n")

        # Create AI config
        ai_config = AIConfig(
            enabled=True,
            provider=AIProvider(provider),
            api_key=api_key,
            model=model,
        )

        # Create Refactron with AI
        refactron = Refactron(ai_config=ai_config)

        # Generate documentation
        docs = refactron.generate_documentation(target, function or "")

        console.print("[bold green]📝 Generated Documentation:[/bold green]")
        console.print(docs)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        console.print("\n[dim]💡 Tips:[/dim]")
        console.print("[dim]- For OpenAI: Set OPENAI_API_KEY environment variable[/dim]")
        console.print("[dim]- For Anthropic: Set ANTHROPIC_API_KEY environment variable[/dim]")
        console.print("[dim]- For Ollama: Install from https://ollama.ai[/dim]")
        raise SystemExit(1)


@ai.command("refactor")
@click.argument("target", type=click.Path(exists=True))
@click.option("--provider", type=click.Choice(["openai", "anthropic", "ollama"]), default="openai")
@click.option("--api-key", help="API key (not needed for Ollama)")
@click.option("--model", help="Model name (optional)")
@click.option("--issue-type", default="general", help="Type of issue to address")
def ai_refactor(
    target: str,
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    issue_type: str,
) -> None:
    """Get AI-powered refactoring suggestions."""
    from refactron.ai import AIConfig, AIProvider

    try:
        console.print(f"[cyan]🤖 Getting refactoring suggestions for {target}...[/cyan]\n")

        # Create AI config
        ai_config = AIConfig(
            enabled=True,
            provider=AIProvider(provider),
            api_key=api_key,
            model=model,
        )

        # Create Refactron with AI
        refactron = Refactron(ai_config=ai_config)

        # Get refactoring suggestions
        refactoring = refactron.get_refactoring_suggestions(target, issue_type)

        console.print("[bold green]🔧 Refactoring Suggestions:[/bold green]")
        console.print(refactoring)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        console.print("\n[dim]💡 Tips:[/dim]")
        console.print("[dim]- For OpenAI: Set OPENAI_API_KEY environment variable[/dim]")
        console.print("[dim]- For Anthropic: Set ANTHROPIC_API_KEY environment variable[/dim]")
        console.print("[dim]- For Ollama: Install from https://ollama.ai[/dim]")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
