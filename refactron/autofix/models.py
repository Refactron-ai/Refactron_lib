"""
Models for auto-fix system.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class FixRiskLevel(Enum):
    """Risk levels for automatic fixes."""

    SAFE = 0.0
    LOW = 0.2
    MODERATE = 0.4
    HIGH = 0.6
    VERY_HIGH = 0.8


@dataclass
class FixResult:
    """Result of an automatic fix."""

    success: bool
    reason: str = ""
    diff: Optional[str] = None
    original: Optional[str] = None
    fixed: Optional[str] = None
    risk_score: float = 1.0
    files_affected: List[str] = None

    def __post_init__(self):
        if self.files_affected is None:
            self.files_affected = []
