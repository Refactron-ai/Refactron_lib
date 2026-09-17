"""Configuration management for Refactron."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from refactron.core.config_loader import ConfigLoader
from refactron.core.config_validator import ConfigValidator
from refactron.core.exceptions import ConfigError


# Valid verification check names, also the default execution order.
DEFAULT_VERIFICATION_CHECKS = ["syntax", "import_integrity", "test_gate"]


@dataclass
class VerificationConfig:
    """Settings for the verification pipeline (`refactron verify`, `--verify`).

    Every default reproduces the historical hard-coded behaviour, so existing
    projects need no migration: a config file with no ``verification:`` section
    behaves exactly as before.

    Fields:
        enabled_checks: Checks to run, in execution order. Any subset (and any
            ordering) of ``syntax``, ``import_integrity``, ``test_gate``. For
            fast PR checks a team might use ``[syntax, import_integrity]`` only.
        short_circuit: Stop after the first failing check (fast) when True;
            run every check for a complete failure report when False.
        test_gate_timeout_sec: Subprocess timeout for the pytest-based test
            gate, in seconds.
        pytest_extra_args: Extra arguments appended to the pytest command line
            (e.g. ``["-p", "no:cacheprovider"]``).
    """

    enabled_checks: List[str] = field(
        default_factory=lambda: list(DEFAULT_VERIFICATION_CHECKS)
    )
    short_circuit: bool = True
    test_gate_timeout_sec: int = 45
    pytest_extra_args: List[str] = field(default_factory=list)


@dataclass
class RefactronConfig:
    """Configuration for Refactron analysis and refactoring."""

    # Configuration metadata
    version: str = field(default_factory=lambda: ConfigValidator.CURRENT_VERSION)
    environment: Optional[str] = None  # dev, staging, prod

    # Analysis settings
    enabled_analyzers: List[str] = field(
        default_factory=lambda: [
            "complexity",
            "code_smells",
            "security",
            "dependency",
            "dead_code",
            "type_hints",
            "performance",
        ]
    )

    # Refactoring settings
    enabled_refactorers: List[str] = field(
        default_factory=lambda: [
            "extract_method",
            "extract_constant",
            "simplify_conditionals",
            "reduce_parameters",
            "add_docstring",
        ]
    )

    # Complexity thresholds
    max_function_complexity: int = 10
    max_function_length: int = 50
    max_file_length: int = 500
    max_parameters: int = 5

    # Reporting settings
    report_format: str = "text"  # text, json, html
    show_details: bool = True

    # Safety settings
    require_preview: bool = True
    backup_enabled: bool = True

    # File patterns
    include_patterns: List[str] = field(default_factory=lambda: ["*.py"])
    exclude_patterns: List[str] = field(
        default_factory=lambda: [
            "**/test_*.py",
            "**/__pycache__/**",
            "**/venv/**",
            "**/env/**",
            "**/.git/**",
            "**/.refactron-backup/**",
        ]
    )

    # Custom rules
    custom_rules: Dict[str, Any] = field(default_factory=dict)

    # Security analyzer settings
    security_ignore_patterns: List[str] = field(
        default_factory=lambda: [
            "**/test_*.py",
            "**/tests/**/*.py",
            "**/*_test.py",
        ]
    )
    security_rule_whitelist: Dict[str, List[str]] = field(default_factory=dict)
    security_min_confidence: float = 0.5  # Minimum confidence to report issues

    # Performance optimization settings
    enable_ast_cache: bool = True
    ast_cache_dir: Optional[Path] = None
    max_ast_cache_size_mb: int = 100

    enable_incremental_analysis: bool = True
    incremental_state_file: Optional[Path] = None

    enable_parallel_processing: bool = True
    max_parallel_workers: Optional[int] = None
    use_multiprocessing: bool = False  # Threading by default (more compatible)

    enable_memory_profiling: bool = False
    memory_optimization_threshold_mb: float = 5.0
    memory_pressure_threshold_percent: float = 80.0
    memory_pressure_threshold_available_mb: float = 500.0
    cache_cleanup_threshold_percent: float = 0.8

    # Logging and monitoring settings
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "text"  # json or text
    log_file: Optional[Path] = None  # If None, uses default location
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB default
    log_backup_count: int = 5
    enable_console_logging: bool = True
    enable_file_logging: bool = True

    # Metrics collection settings
    enable_metrics: bool = True
    metrics_detailed: bool = True  # Track detailed per-file metrics

    # Prometheus settings
    enable_prometheus: bool = False
    prometheus_host: str = "127.0.0.1"
    prometheus_port: int = 9090

    # Telemetry settings
    enable_telemetry: bool = False  # Opt-in only
    telemetry_endpoint: Optional[str] = None  # For future remote submission

    # Pattern learning settings
    enable_pattern_learning: bool = True  # Master switch for pattern learning
    pattern_storage_dir: Optional[Path] = None  # Custom storage directory (None = default)
    pattern_learning_enabled: bool = True  # Enable learning from feedback
    pattern_ranking_enabled: bool = True  # Enable ranking based on learned patterns

    # Verification pipeline settings (refactron verify / autofix --verify)
    verification: VerificationConfig = field(default_factory=VerificationConfig)

    @classmethod
    def from_file(
        cls,
        config_path: Path,
        profile: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> "RefactronConfig":
        """Load configuration from a YAML file with profile and environment support.

        Args:
            config_path: Path to the YAML configuration file
            profile: Profile name to use (dev, staging, prod). Overridden by environment.
            environment: Environment name (dev, staging, prod). Takes precedence over profile.

        Returns:
            RefactronConfig instance with loaded settings

        Raises:
            ConfigError: If config file cannot be loaded or parsed
        """
        # Use enhanced config loader with profile and environment support
        config_dict = ConfigLoader.load_from_file(config_path, profile, environment)

        # Convert path strings to Path objects
        path_fields = [
            "ast_cache_dir",
            "incremental_state_file",
            "log_file",
            "pattern_storage_dir",
        ]
        for path_field in path_fields:
            if (
                path_field in config_dict
                and config_dict[path_field]
                and isinstance(config_dict[path_field], str)
            ):
                config_dict[path_field] = Path(config_dict[path_field])

        # Convert the nested `verification:` mapping into its dataclass.
        if isinstance(config_dict.get("verification"), dict):
            try:
                config_dict["verification"] = VerificationConfig(
                    **config_dict["verification"]
                )
            except TypeError as e:
                raise ConfigError(
                    f"Invalid 'verification' configuration: {e}",
                    config_path=config_path,
                    recovery_suggestion=(
                        "Valid keys: enabled_checks, short_circuit, "
                        "test_gate_timeout_sec, pytest_extra_args."
                    ),
                ) from e

        try:
            return cls(**config_dict)
        except TypeError as e:
            raise ConfigError(
                f"Invalid configuration options: {e}",
                config_path=config_path,
                recovery_suggestion=(
                    "Check that all configuration fields match the expected types. "
                    "Run 'refactron init' to generate a valid template."
                ),
            ) from e

    def to_file(self, config_path: Path) -> None:
        """Save configuration to a YAML file.

        Args:
            config_path: Path where configuration should be saved

        Raises:
            ConfigError: If config file cannot be written
        """
        config_dict = {
            "version": self.version,
            "environment": self.environment,
            "enabled_analyzers": self.enabled_analyzers,
            "enabled_refactorers": self.enabled_refactorers,
            "max_function_complexity": self.max_function_complexity,
            "max_function_length": self.max_function_length,
            "max_file_length": self.max_file_length,
            "max_parameters": self.max_parameters,
            "report_format": self.report_format,
            "show_details": self.show_details,
            "require_preview": self.require_preview,
            "backup_enabled": self.backup_enabled,
            "include_patterns": self.include_patterns,
            "exclude_patterns": self.exclude_patterns,
            "custom_rules": self.custom_rules,
            "security_ignore_patterns": self.security_ignore_patterns,
            "security_rule_whitelist": self.security_rule_whitelist,
            "security_min_confidence": self.security_min_confidence,
            "enable_ast_cache": self.enable_ast_cache,
            "ast_cache_dir": str(self.ast_cache_dir) if self.ast_cache_dir else None,
            "max_ast_cache_size_mb": self.max_ast_cache_size_mb,
            "enable_incremental_analysis": self.enable_incremental_analysis,
            "incremental_state_file": (
                str(self.incremental_state_file) if self.incremental_state_file else None
            ),
            "enable_parallel_processing": self.enable_parallel_processing,
            "max_parallel_workers": self.max_parallel_workers,
            "use_multiprocessing": self.use_multiprocessing,
            "enable_memory_profiling": self.enable_memory_profiling,
            "memory_optimization_threshold_mb": self.memory_optimization_threshold_mb,
            "memory_pressure_threshold_percent": self.memory_pressure_threshold_percent,
            "memory_pressure_threshold_available_mb": self.memory_pressure_threshold_available_mb,
            "cache_cleanup_threshold_percent": self.cache_cleanup_threshold_percent,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "log_file": str(self.log_file) if self.log_file else None,
            "log_max_bytes": self.log_max_bytes,
            "log_backup_count": self.log_backup_count,
            "enable_console_logging": self.enable_console_logging,
            "enable_file_logging": self.enable_file_logging,
            "enable_metrics": self.enable_metrics,
            "metrics_detailed": self.metrics_detailed,
            "enable_prometheus": self.enable_prometheus,
            "prometheus_host": self.prometheus_host,
            "prometheus_port": self.prometheus_port,
            "enable_telemetry": self.enable_telemetry,
            "telemetry_endpoint": self.telemetry_endpoint,
            "enable_pattern_learning": self.enable_pattern_learning,
            "pattern_storage_dir": (
                str(self.pattern_storage_dir) if self.pattern_storage_dir else None
            ),
            "pattern_learning_enabled": self.pattern_learning_enabled,
            "pattern_ranking_enabled": self.pattern_ranking_enabled,
            "verification": {
                "enabled_checks": self.verification.enabled_checks,
                "short_circuit": self.verification.short_circuit,
                "test_gate_timeout_sec": self.verification.test_gate_timeout_sec,
                "pytest_extra_args": self.verification.pytest_extra_args,
            },
        }

        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        except (IOError, OSError) as e:
            raise ConfigError(
                f"Failed to write configuration file: {e}",
                config_path=config_path,
            ) from e

    @classmethod
    def default(cls) -> "RefactronConfig":
        """Return default configuration."""
        return cls()
