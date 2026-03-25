"""
Shared utility functions for the Refactron CLI.
Includes configuration loading, logging setup, and API validation.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests  # type: ignore

from refactron.cli.ui import console
from refactron.core.config import RefactronConfig
from refactron.core.exceptions import ConfigError
from refactron.patterns.storage import PatternStorage


@dataclass(frozen=True)
class ApiKeyValidationResult:
    ok: bool
    message: str


def _validate_api_key(
    api_base_url: str, api_key: str, timeout_seconds: int
) -> ApiKeyValidationResult:
    """
    Validate an API key against the backend before saving it locally.

    The key is sent as a Bearer token to a small verification endpoint. We keep
    the UX actionable: distinguish invalid keys from missing endpoints and
    connectivity issues.
    """
    url = f"{api_base_url.rstrip('/')}/api/auth/verify-key"
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout_seconds,
        )
    except requests.Timeout:
        return ApiKeyValidationResult(
            ok=False,
            message="API key verification timed out. Is the API reachable?",
        )
    except requests.ConnectionError:
        return ApiKeyValidationResult(
            ok=False,
            message="Could not reach the Refactron API. Is it running?",
        )
    except requests.RequestException:
        return ApiKeyValidationResult(
            ok=False,
            message="API key verification failed due to a network error.",
        )

    if response.status_code == 200:
        return ApiKeyValidationResult(ok=True, message="Verified.")
    if response.status_code in (401, 403):
        return ApiKeyValidationResult(ok=False, message="Invalid API key.")
    if response.status_code == 404:
        return ApiKeyValidationResult(
            ok=False,
            message="API key verification endpoint is missing (404).",
        )
    if 500 <= response.status_code <= 599:
        return ApiKeyValidationResult(
            ok=False,
            message=f"API key verification failed (server error {response.status_code}).",
        )
    return ApiKeyValidationResult(
        ok=False,
        message=f"API key verification failed (HTTP {response.status_code}).",
    )


def _setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO

    # Remove duplicate handlers that accumulate when basicConfig is called
    # multiple times (e.g. from tests or repeated CLI invocations).
    root = logging.getLogger()
    root.handlers.clear()

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    # Suppress refactron internal logs during CLI (INFO/DEBUG are diagnostics, not user output).
    # Users can override with --log-level DEBUG/INFO.
    if not verbose:
        logging.getLogger("refactron").setLevel(logging.WARNING)

    # Suppress noisy third-party libraries
    if not verbose:
        # Standard logging suppression
        for logger_name in [
            "httpx",
            "sentence_transformers",
            "transformers",
            "tokenizers",
            "chromadb",
            "huggingface_hub",
        ]:
            logging.getLogger(logger_name).setLevel(logging.ERROR)

        # Specific suppression for transformers library to avoid "Load Report"
        try:
            from transformers import logging as tf_logging

            tf_logging.set_verbosity_error()
        except ImportError:
            pass


def _load_config(
    config_path: Optional[str],
    profile: Optional[str] = None,
    environment: Optional[str] = None,
) -> RefactronConfig:
    """Load configuration from file or use default."""
    try:
        if config_path:
            console.print(f"[dim]Loading config from: {config_path}[/dim]")
            if profile or environment:
                env_display = environment or profile
                console.print(f"[dim]Using profile/environment: {env_display}[/dim]")
            return RefactronConfig.from_file(Path(config_path), profile, environment)
        return RefactronConfig.default()
    except ConfigError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        if e.recovery_suggestion:
            console.print(f"[yellow]Tip: {e.recovery_suggestion}[/yellow]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error loading configuration: {e}[/red]")
        raise SystemExit(1)


def _validate_path(target: str) -> Path:
    """Validate target path exists."""
    target_path = Path(target)
    if not target_path.exists():
        console.print(f"[red]Error: Path does not exist: {target}[/red]")
        raise SystemExit(1)
    return target_path


def _detect_project_type() -> Optional[str]:
    """
    Detect project type by checking for framework-specific files and imports.

    Detection patterns:
    - Django: Checks for settings.py or manage.py files with Django-specific imports/variables
    - FastAPI: Looks for 'from fastapi import' or 'import fastapi' in common entry points
    - Flask: Looks for 'from flask import' with Flask app instantiation patterns

    Returns:
        Detected framework name ('django', 'fastapi', 'flask') or None
    """
    current_dir = Path.cwd()

    # Check for Django first (manage.py or settings.py are strong signals)
    for django_file in ["manage.py", "**/settings.py"]:
        for file_path in current_dir.glob(django_file):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    # Read line by line to avoid loading large files
                    for line in f:
                        if "django" in line.lower() or "DJANGO_SETTINGS_MODULE" in line:
                            return "django"
            except (IOError, OSError):
                pass

    # Check common entry point files for FastAPI and Flask
    common_entry_points = [
        "main.py",
        "app.py",
        "application.py",
        "server.py",
        "api.py",
    ]
    for entry_point in common_entry_points:
        for file_path in current_dir.glob(entry_point):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Check for FastAPI
                    if "from fastapi import" in content or "import fastapi" in content:
                        return "fastapi"

                    # Check for Flask
                    if "from flask import" in content or "import flask" in content:
                        if "Flask(__name__)" in content or "app = Flask" in content:
                            return "flask"
            except (IOError, OSError):
                pass

    return None


def _get_pattern_storage_from_config(
    config: RefactronConfig,
) -> Optional[PatternStorage]:
    """Get PatternStorage instance if enabled in config."""
    if config.enable_pattern_learning:
        return PatternStorage(config.pattern_storage_dir)
    return None
