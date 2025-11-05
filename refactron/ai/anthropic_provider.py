"""Anthropic/Claude provider for AI-powered features."""

import os

from refactron.ai.base import AIConfig, BaseAIProvider


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude-based AI provider."""

    def __init__(self, config: AIConfig):
        """Initialize Anthropic provider."""
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = config.model or "claude-3-5-sonnet-20241022"

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY env var or provide in config."
            )

        try:
            import anthropic

            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Install with: pip install anthropic"
            )

    def _call_api(self, prompt: str, system_prompt: str = "") -> str:
        """Call Anthropic API with the given prompt."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt if system_prompt else "You are a helpful Python expert.",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error calling Anthropic API: {str(e)}"

    def generate_docstring(self, code: str, context: str = "") -> str:
        """Generate docstring for code using Claude."""
        system_prompt = (
            "You are a Python documentation expert. Generate concise, "
            "clear docstrings following Google style guide."
        )

        prompt = f"""Generate a docstring for the following Python code:

```python
{code}
```

{f"Context: {context}" if context else ""}

Return only the docstring text without code fences or additional explanation."""

        return self._call_api(prompt, system_prompt)

    def explain_code(self, code: str) -> str:
        """Explain what the code does."""
        system_prompt = "You are a Python expert. Explain code clearly and concisely."

        prompt = f"""Explain what this Python code does:

```python
{code}
```

Provide a clear, concise explanation suitable for developers."""

        return self._call_api(prompt, system_prompt)

    def suggest_improvements(self, code: str, issues: list) -> str:
        """Suggest improvements based on code analysis."""
        system_prompt = (
            "You are a Python code quality expert. "
            "Provide actionable suggestions for code improvements."
        )

        issues_text = "\n".join([f"- {issue}" for issue in issues])

        prompt = f"""The following Python code has these issues:
{issues_text}

Code:
```python
{code}
```

Suggest specific, actionable improvements to address these issues."""

        return self._call_api(prompt, system_prompt)

    def optimize_code(self, code: str) -> str:
        """Suggest optimizations for the code."""
        system_prompt = (
            "You are a Python performance expert. "
            "Suggest practical optimizations for code efficiency."
        )

        prompt = f"""Analyze this Python code for potential optimizations:

```python
{code}
```

Suggest specific optimizations for:
1. Performance improvements
2. Memory efficiency
3. Readability
4. Best practices

Focus on practical, implementable suggestions."""

        return self._call_api(prompt, system_prompt)

    def generate_refactoring_suggestion(self, code: str, issue_type: str) -> str:
        """Generate specific refactoring suggestions."""
        system_prompt = (
            "You are a Python refactoring expert. "
            "Provide specific refactoring recommendations with code examples."
        )

        prompt = f"""Suggest refactoring for this code with issue type: {issue_type}

Code:
```python
{code}
```

Provide:
1. What's wrong with the current code
2. Specific refactoring steps
3. Example of refactored code
4. Benefits of the refactoring"""

        return self._call_api(prompt, system_prompt)
