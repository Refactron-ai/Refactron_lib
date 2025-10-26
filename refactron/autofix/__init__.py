"""
Auto-fix module for automatically fixing code issues.

This module provides rule-based code fixes without requiring expensive AI APIs.
All fixers use AST analysis and pattern matching for fast, reliable transformations.
"""

from refactron.autofix.engine import AutoFixEngine, FixResult
from refactron.autofix.fixers import (
    AddDocstringsFixer,
    ExtractMagicNumbersFixer,
    FixTypeHintsFixer,
    RemoveDeadCodeFixer,
    RemoveUnusedImportsFixer,
)

__all__ = [
    "AutoFixEngine",
    "FixResult",
    "RemoveUnusedImportsFixer",
    "ExtractMagicNumbersFixer",
    "AddDocstringsFixer",
    "RemoveDeadCodeFixer",
    "FixTypeHintsFixer",
]
