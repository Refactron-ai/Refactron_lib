"""Base classes for AI providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AIProvider(Enum):
    """Supported AI providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LOCAL = "local"


@dataclass
class AIConfig:
    """Configuration for AI features."""

    enabled: bool = False
    provider: AIProvider = AIProvider.OPENAI
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30


class BaseAIProvider(ABC):
    """Base class for AI providers."""

    def __init__(self, config: AIConfig):
        """Initialize the AI provider."""
        self.config = config

    @abstractmethod
    def generate_docstring(self, code: str, context: str = "") -> str:
        """Generate docstring for code."""
        pass

    @abstractmethod
    def explain_code(self, code: str) -> str:
        """Explain what the code does."""
        pass

    @abstractmethod
    def suggest_improvements(self, code: str, issues: list) -> str:
        """Suggest improvements based on code analysis."""
        pass

    @abstractmethod
    def optimize_code(self, code: str) -> str:
        """Suggest optimizations for the code."""
        pass

    @abstractmethod
    def generate_refactoring_suggestion(self, code: str, issue_type: str) -> str:
        """Generate specific refactoring suggestions."""
        pass
