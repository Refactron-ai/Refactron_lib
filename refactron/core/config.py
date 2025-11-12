"""Configuration management for Refactron."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class RefactronConfig:
    """Configuration for Refactron analysis and refactoring."""

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

    @classmethod
    def from_file(cls, config_path: Path) -> "RefactronConfig":
        """Load configuration from a YAML file."""
        if not config_path.exists():
            return cls()

        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f) or {}

        return cls(**config_dict)

    def to_file(self, config_path: Path) -> None:
        """Save configuration to a YAML file."""
        config_dict = {
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
        }

        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)

    @classmethod
    def default(cls) -> "RefactronConfig":
        """Return default configuration."""
        return cls()
