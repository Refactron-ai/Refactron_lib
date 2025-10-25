"""Analysis result representation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from refactron.core.models import CodeIssue, FileMetrics, IssueLevel


@dataclass
class AnalysisResult:
    """Result of code analysis."""

    file_metrics: List[FileMetrics] = field(default_factory=list)
    total_files: int = 0
    total_issues: int = 0

    @property
    def critical_issues(self) -> List[CodeIssue]:
        """Get all critical issues across all files."""
        issues = []
        for metrics in self.file_metrics:
            issues.extend(metrics.critical_issues)
        return issues

    @property
    def error_issues(self) -> List[CodeIssue]:
        """Get all error-level issues across all files."""
        issues = []
        for metrics in self.file_metrics:
            issues.extend(metrics.error_issues)
        return issues

    @property
    def all_issues(self) -> List[CodeIssue]:
        """Get all issues across all files."""
        issues = []
        for metrics in self.file_metrics:
            issues.extend(metrics.issues)
        return issues

    def issues_by_level(self, level: IssueLevel) -> List[CodeIssue]:
        """Get issues filtered by severity level."""
        return [issue for issue in self.all_issues if issue.level == level]

    def issues_by_file(self, file_path: Path) -> List[CodeIssue]:
        """Get issues for a specific file."""
        for metrics in self.file_metrics:
            if metrics.file_path == file_path:
                return metrics.issues
        return []

    def summary(self) -> Dict[str, int]:
        """Get a summary of the analysis."""
        return {
            "total_files": self.total_files,
            "total_issues": self.total_issues,
            "critical": len(self.critical_issues),
            "errors": len(self.error_issues),
            "warnings": len(self.issues_by_level(IssueLevel.WARNING)),
            "info": len(self.issues_by_level(IssueLevel.INFO)),
        }

    def report(self, detailed: bool = True) -> str:
        """Generate a text report of the analysis."""
        lines = []
        lines.append("=" * 80)
        lines.append("REFACTRON ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")

        summary = self.summary()
        lines.append(f"📊 Files Analyzed: {summary['total_files']}")
        lines.append(f"⚠️  Total Issues: {summary['total_issues']}")
        lines.append("")
        lines.append("Issues by Severity:")
        lines.append(f"  🔴 Critical: {summary['critical']}")
        lines.append(f"  ❌ Errors: {summary['errors']}")
        lines.append(f"  ⚡ Warnings: {summary['warnings']}")
        lines.append(f"  ℹ️  Info: {summary['info']}")
        lines.append("")

        if detailed and self.all_issues:
            lines.append("-" * 80)
            lines.append("DETAILED ISSUES")
            lines.append("-" * 80)
            lines.append("")

            for issue in self.all_issues:
                lines.append(str(issue))
                if issue.suggestion:
                    lines.append(f"  💡 Suggestion: {issue.suggestion}")
                lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)
