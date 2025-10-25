"""Base refactorer class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from refactron.core.config import RefactronConfig
from refactron.core.models import RefactoringOperation


class BaseRefactorer(ABC):
    """Base class for all refactorers."""

    def __init__(self, config: RefactronConfig):
        """
        Initialize the refactorer.

        Args:
            config: Refactron configuration
        """
        self.config = config

    @abstractmethod
    def refactor(self, file_path: Path, source_code: str) -> List[RefactoringOperation]:
        """
        Analyze source code and return refactoring operations.

        Args:
            file_path: Path to the file being refactored
            source_code: Source code content

        Returns:
            List of refactoring operations
        """
        pass

    @property
    @abstractmethod
    def operation_type(self) -> str:
        """Return the type of refactoring this performs."""
        pass
