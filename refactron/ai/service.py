"""AI service manager and factory."""

from typing import Optional

from refactron.ai.base import AIConfig, AIProvider, BaseAIProvider


class AIService:
    """
    Service for AI-powered code analysis and suggestions.

    This service supports multiple AI providers:
    - OpenAI (GPT models) - requires API key
    - Anthropic (Claude models) - requires API key
    - Ollama (local models) - free, no API key needed
    """

    def __init__(self, config: Optional[AIConfig] = None):
        """
        Initialize AI service.

        Args:
            config: AI configuration. If None, AI features are disabled.
        """
        self.config = config or AIConfig(enabled=False)
        self.provider: Optional[BaseAIProvider] = None

        if self.config.enabled:
            self.provider = self._create_provider()

    def _create_provider(self) -> BaseAIProvider:
        """Create the appropriate AI provider based on configuration."""
        if self.config.provider == AIProvider.OPENAI:
            from refactron.ai.openai_provider import OpenAIProvider

            return OpenAIProvider(self.config)
        elif self.config.provider == AIProvider.ANTHROPIC:
            from refactron.ai.anthropic_provider import AnthropicProvider

            return AnthropicProvider(self.config)
        elif self.config.provider == AIProvider.OLLAMA:
            from refactron.ai.ollama_provider import OllamaProvider

            return OllamaProvider(self.config)
        else:
            raise ValueError(f"Unsupported AI provider: {self.config.provider}")

    def is_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return self.config.enabled and self.provider is not None

    def generate_docstring(self, code: str, context: str = "") -> str:
        """
        Generate docstring for code using AI.

        Args:
            code: The code to document
            context: Additional context about the code

        Returns:
            Generated docstring

        Raises:
            RuntimeError: If AI features are not enabled
        """
        if not self.is_enabled():
            raise RuntimeError("AI features not enabled. Configure AI provider first.")

        return self.provider.generate_docstring(code, context)

    def explain_code(self, code: str) -> str:
        """
        Explain what the code does using AI.

        Args:
            code: The code to explain

        Returns:
            Code explanation

        Raises:
            RuntimeError: If AI features are not enabled
        """
        if not self.is_enabled():
            raise RuntimeError("AI features not enabled. Configure AI provider first.")

        return self.provider.explain_code(code)

    def suggest_improvements(self, code: str, issues: list) -> str:
        """
        Suggest improvements for code based on detected issues.

        Args:
            code: The code to improve
            issues: List of detected issues

        Returns:
            Improvement suggestions

        Raises:
            RuntimeError: If AI features are not enabled
        """
        if not self.is_enabled():
            raise RuntimeError("AI features not enabled. Configure AI provider first.")

        return self.provider.suggest_improvements(code, issues)

    def optimize_code(self, code: str) -> str:
        """
        Suggest optimizations for the code.

        Args:
            code: The code to optimize

        Returns:
            Optimization suggestions

        Raises:
            RuntimeError: If AI features are not enabled
        """
        if not self.is_enabled():
            raise RuntimeError("AI features not enabled. Configure AI provider first.")

        return self.provider.optimize_code(code)

    def generate_refactoring_suggestion(self, code: str, issue_type: str) -> str:
        """
        Generate specific refactoring suggestions.

        Args:
            code: The code to refactor
            issue_type: The type of issue to address

        Returns:
            Refactoring suggestions

        Raises:
            RuntimeError: If AI features are not enabled
        """
        if not self.is_enabled():
            raise RuntimeError("AI features not enabled. Configure AI provider first.")

        return self.provider.generate_refactoring_suggestion(code, issue_type)


def create_ai_service(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs,
) -> AIService:
    """
    Factory function to create an AI service.

    Args:
        provider: AI provider name ('openai', 'anthropic', 'ollama')
        api_key: API key (not needed for Ollama)
        model: Model name (optional, uses defaults)
        **kwargs: Additional configuration options

    Returns:
        Configured AIService instance

    Example:
        >>> # Using OpenAI
        >>> service = create_ai_service('openai', api_key='sk-...')
        >>>
        >>> # Using Ollama (local, free)
        >>> service = create_ai_service('ollama', model='codellama')
    """
    # Convert string provider to AIProvider enum
    provider_lower = provider.lower()
    try:
        provider_enum = AIProvider[provider_lower.upper()]
    except KeyError:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Must be one of: {', '.join([p.value for p in AIProvider])}"
        )

    config = AIConfig(
        enabled=True,
        provider=provider_enum,
        api_key=api_key,
        model=model,
        **kwargs,
    )
    return AIService(config)
