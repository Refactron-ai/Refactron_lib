"""Base analyzer class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from refactron.core.config import RefactronConfig
from refactron.core.models import CodeIssue


class BaseAnalyzer(ABC):
    """Base class for all analyzers."""

    def __init__(self, config: RefactronConfig):
        """
        Initialize the analyzer.

        Args:
            config: Refactron configuration
        """
        self.config = config

    @abstractmethod
    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze source code and return detected issues.

        Args:
            file_path: Path to the file being analyzed
            source_code: Source code content

        Returns:
            List of detected code issues
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this analyzer."""
        pass
