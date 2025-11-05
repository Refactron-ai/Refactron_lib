"""
Refactron - The Intelligent Code Refactoring Transformer

A powerful Python library for code refactoring, optimization, and technical debt elimination.
"""

from refactron.ai import AIConfig, AIProvider, AIService, create_ai_service
from refactron.core.analysis_result import AnalysisResult
from refactron.core.refactor_result import RefactorResult
from refactron.core.refactron import Refactron

__version__ = "1.0.0"
__author__ = "Om Sherikar"

__all__ = [
    "Refactron",
    "AnalysisResult",
    "RefactorResult",
    "AIService",
    "AIConfig",
    "AIProvider",
    "create_ai_service",
]
