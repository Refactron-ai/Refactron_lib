"""Data models for custom rules."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class PatternType(Enum):
    """Types of patterns that can be matched."""

    FUNCTION_CALL = "function_call"
    CLASS_DEF = "class_def"
    FUNCTION_DEF = "function_def"
    IMPORT = "import"
    ATTRIBUTE = "attribute"
    REGEX = "regex"
    AST_PATTERN = "ast_pattern"


class RuleSeverity(Enum):
    """Severity levels for custom rules."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PatternConfig:
    """Configuration for a pattern to match."""

    type: PatternType
    # For function_call, class_def, function_def, attribute
    name: Optional[str] = None
    # For regex patterns
    regex: Optional[str] = None
    # For AST patterns
    ast_pattern: Optional[Dict[str, Any]] = None
    # Additional constraints
    constraints: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatternConfig":
        """Create PatternConfig from dictionary."""
        pattern_type = PatternType(data.get("type", "function_call"))
        return cls(
            type=pattern_type,
            name=data.get("name"),
            regex=data.get("regex"),
            ast_pattern=data.get("ast_pattern"),
            constraints=data.get("constraints", {}),
        )


@dataclass
class CustomRule:
    """Represents a custom analysis rule."""

    name: str
    description: str
    severity: RuleSeverity
    pattern: PatternConfig
    message: str
    suggestion: Optional[str] = None
    exclude: List[str] = field(default_factory=list)
    include: List[str] = field(default_factory=list)
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomRule":
        """Create CustomRule from dictionary."""
        severity = RuleSeverity(data.get("severity", "warning"))
        pattern = PatternConfig.from_dict(data.get("pattern", {}))

        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            severity=severity,
            pattern=pattern,
            message=data.get("message", ""),
            suggestion=data.get("suggestion"),
            exclude=data.get("exclude", []),
            include=data.get("include", []),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class RuleSet:
    """Collection of custom rules."""

    version: str
    rules: List[CustomRule] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleSet":
        """Create RuleSet from dictionary."""
        rules = [CustomRule.from_dict(rule_data) for rule_data in data.get("rules", [])]
        return cls(
            version=data.get("version", "1"),
            rules=rules,
            metadata=data.get("metadata", {}),
        )
