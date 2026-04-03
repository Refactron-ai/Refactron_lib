"""
Refactron CLI - Main Entry Point.
Defines the main Click group, handles authentication checks, and registers subcommands.
"""

from datetime import datetime, timezone

import click
from rich.align import Align
from rich.prompt import Prompt
from rich.text import Text

from refactron import __version__
from refactron.cli.ui import _print_custom_help, _run_minimal_loop, _run_startup_animation, console
from refactron.core.credentials import load_credentials
from refactron.core.device_auth import DEFAULT_API_BASE_URL


class CustomHelpGroup(click.Group):
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        _print_custom_help(ctx)


@click.group(cls=CustomHelpGroup, invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """
    Refactron - The Intelligent Code Refactoring Transformer

    Analyze, refactor, and optimize your Python code with ease.
    """
    # Check authentication for all commands except login/logout
    exempt_commands = ["login", "logout", "auth"]

    # 1. Pre-check authentication status
    creds = load_credentials()
    is_authenticated = False
    if creds and creds.access_token:
        now = datetime.now(timezone.utc)
        if not creds.expires_at or creds.expires_at > now:
            is_authenticated = True

    # 2. Show animation if dashboard mode OR if auth is required and missing
    should_show_animation = ctx.invoked_subcommand is None or (
        ctx.invoked_subcommand not in exempt_commands and not is_authenticated
    )

    if should_show_animation:
        _run_startup_animation()

    # 3. Handle authentication requirement
    if ctx.invoked_subcommand not in exempt_commands and not is_authenticated:
        # If it's a subcommand, we might want a slightly different message
        if ctx.invoked_subcommand:
            console.print(
                f"\n[yellow]Authentication required to run '{ctx.invoked_subcommand}'[/yellow]"
            )
        else:
            console.print(Align.center(Text("\nAuthentication Required", style="bold")))

        if Prompt.ask("\nLog in to continue?", choices=["y", "n"], default="y") == "y":
            try:
                # We need to import login here to avoid circular dependencies
                from refactron.cli.auth import login

                ctx.invoke(
                    login,
                    api_base_url=DEFAULT_API_BASE_URL,
                    no_browser=False,
                    timeout=300,
                    force=False,
                )
                # Re-check credentials
                creds = load_credentials()
                if creds and creds.access_token:
                    is_authenticated = True
            except SystemExit:
                pass

        if not is_authenticated:
            console.print("[dim]Exiting...[/dim]")
            raise SystemExit(1)

    # 4. Handle default command (interactive dashboard)
    if ctx.invoked_subcommand is None:
        _run_minimal_loop(ctx)
    pass


# Register subcommands
# We import them here to ensure they are registered with the main group
# Using a try-except block to allow partial loading during refactoring
try:
    from refactron.cli.auth import auth, login, logout, telemetry

    main.add_command(login)
    main.add_command(logout)
    main.add_command(auth)
    main.add_command(telemetry)
except ImportError:
    pass

try:
    from refactron.cli.analysis import analyze, metrics, report, serve_metrics, suggest
    from refactron.cli.verify import verify

    main.add_command(analyze)
    main.add_command(verify)
    main.add_command(report)
    main.add_command(metrics)
    main.add_command(serve_metrics)
    main.add_command(suggest)
except ImportError:
    pass

try:
    from refactron.cli.refactor import autofix, document, refactor, rollback

    main.add_command(refactor)
    main.add_command(autofix)
    main.add_command(rollback)
    main.add_command(document)
except ImportError:
    pass

try:
    from refactron.cli.patterns import patterns

    main.add_command(patterns)
except ImportError:
    pass

try:
    from refactron.cli.repo import repo

    main.add_command(repo)
except ImportError:
    pass

try:
    from refactron.cli.rag import rag

    main.add_command(rag)
except ImportError:
    pass

try:
    from refactron.cli.cicd import feedback, generate_cicd, init

    main.add_command(generate_cicd)
    main.add_command(feedback)
    main.add_command(init)
except ImportError:
    pass
