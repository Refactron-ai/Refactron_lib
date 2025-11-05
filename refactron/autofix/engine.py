"""
Auto-fix engine for applying rule-based code transformations.

This engine uses AST analysis and pattern matching to apply safe
automatic fixes without requiring expensive AI APIs.
"""

from typing import Dict

from refactron.autofix.models import FixResult, FixRiskLevel
from refactron.core.models import CodeIssue


class AutoFixEngine:
    """
    Engine for applying automatic fixes to code issues.

    All fixes use rule-based AST transformations for reliability
    and performance. No expensive AI APIs required!
    """

    def __init__(self, safety_level: FixRiskLevel = FixRiskLevel.SAFE):
        """
        Initialize the auto-fix engine.

        Args:
            safety_level: Maximum risk level to apply automatically
        """
        self.safety_level = safety_level
        self.fixers = self._register_fixers()

    def _register_fixers(self) -> Dict[str, "BaseFixer"]:
        """Register all available fixers."""
        from refactron.autofix.fixers import (
            AddDocstringsFixer,
            AddMissingCommasFixer,
            ConvertToFStringFixer,
            ExtractMagicNumbersFixer,
            FixIndentationFixer,
            FixTypeHintsFixer,
            NormalizeQuotesFixer,
            RemoveDeadCodeFixer,
            RemovePrintStatementsFixer,
            RemoveTrailingWhitespaceFixer,
            RemoveUnusedImportsFixer,
            RemoveUnusedVariablesFixer,
            SimplifyBooleanFixer,
            SortImportsFixer,
        )

        fixers = {}
        for fixer_class in [
            RemoveUnusedImportsFixer,
            ExtractMagicNumbersFixer,
            AddDocstringsFixer,
            RemoveDeadCodeFixer,
            FixTypeHintsFixer,
            SortImportsFixer,
            RemoveTrailingWhitespaceFixer,
            NormalizeQuotesFixer,
            SimplifyBooleanFixer,
            ConvertToFStringFixer,
            RemoveUnusedVariablesFixer,
            FixIndentationFixer,
            AddMissingCommasFixer,
            RemovePrintStatementsFixer,
        ]:
            fixer = fixer_class()
            fixers[fixer.name] = fixer

        return fixers

    def can_fix(self, issue: CodeIssue) -> bool:
        """
        Check if an issue can be auto-fixed.

        Args:
            issue: The issue to check

        Returns:
            True if a fixer is available, False otherwise
        """
        return issue.rule_id in self.fixers if issue.rule_id else False

    def fix(self, issue: CodeIssue, code: str, preview: bool = True) -> FixResult:
        """
        Apply automatic fix to an issue.

        Args:
            issue: The issue to fix
            code: The original code
            preview: If True, only preview changes (don't apply)

        Returns:
            FixResult with success status and details
        """
        if not self.can_fix(issue):
            return FixResult(
                success=False, reason=f"No fixer available for issue: {issue.rule_id or 'unknown'}"
            )

        fixer = self.fixers[issue.rule_id]

        # Check risk level
        if fixer.risk_score > self.safety_level.value:
            return FixResult(
                success=False,
                reason=(
                    f"Fix risk level ({fixer.risk_score}) exceeds safety level "
                    f"({self.safety_level.value})"
                ),
            )

        # Apply fix
        if preview:
            return fixer.preview(issue, code)
        return fixer.apply(issue, code)

    def fix_all(self, issues: list, code: str, preview: bool = True) -> Dict[int, FixResult]:
        """
        Apply fixes to multiple issues.

        Args:
            issues: List of issues to fix
            code: The original code
            preview: If True, only preview changes

        Returns:
            Dictionary mapping issue index to fix result
        """
        results = {}

        for idx, issue in enumerate(issues):
            if self.can_fix(issue):
                results[idx] = self.fix(issue, code, preview)
            else:
                results[idx] = FixResult(success=False, reason="No fixer available")

        return results


class BaseFixer:
    """Base class for all automatic fixers."""

    def __init__(self, name: str, risk_score: float = 0.0):
        """
        Initialize a fixer.

        Args:
            name: Name of the fixer
            risk_score: Risk level (0.0 = safe, 1.0 = dangerous)
        """
        self.name = name
        self.risk_score = risk_score

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """
        Preview the fix without applying it.

        Args:
            issue: The issue to fix
            code: The original code

        Returns:
            FixResult with diff showing proposed changes
        """
        raise NotImplementedError

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """
        Apply the fix.

        Args:
            issue: The issue to fix
            code: The original code

        Returns:
            FixResult with fixed code
        """
        raise NotImplementedError
