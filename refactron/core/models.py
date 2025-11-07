"""Data models for Refactron."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class IssueLevel(Enum):
    """Severity level of code issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueCategory(Enum):
    """Categories of code issues."""

    COMPLEXITY = "complexity"
    CODE_SMELL = "code_smell"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    STYLE = "style"
    TYPE_HINTS = "type_hints"
    MODERNIZATION = "modernization"
    DEPENDENCY = "dependency"
    DEAD_CODE = "dead_code"


@dataclass
class CodeIssue:
    """Represents a detected code issue."""

    category: IssueCategory
    level: IssueLevel
    message: str
    file_path: Path
    line_number: int
    column: int = 0
    end_line: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None
    confidence: float = 1.0  # Confidence score 0.0-1.0 (1.0 = high confidence)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        location = f"{self.file_path}:{self.line_number}:{self.column}"
        return f"[{self.level.value.upper()}] {location} - {self.message}"


@dataclass
class FileMetrics:
    """Metrics for a single file."""

    file_path: Path
    lines_of_code: int
    comment_lines: int
    blank_lines: int
    complexity: float
    maintainability_index: float
    functions: int
    classes: int
    issues: List[CodeIssue] = field(default_factory=list)

    @property
    def total_lines(self) -> int:
        return self.lines_of_code + self.comment_lines + self.blank_lines

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def critical_issues(self) -> List[CodeIssue]:
        return [i for i in self.issues if i.level == IssueLevel.CRITICAL]

    @property
    def error_issues(self) -> List[CodeIssue]:
        return [i for i in self.issues if i.level == IssueLevel.ERROR]


@dataclass
class RefactoringOperation:
    """Represents a refactoring operation to be applied."""

    operation_type: str
    file_path: Path
    line_number: int
    description: str
    old_code: str
    new_code: str
    risk_score: float  # 0.0 (safe) to 1.0 (risky)
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"{self.operation_type} at {self.file_path}:{self.line_number} "
            f"(risk: {self.risk_score:.2f})"
        )
