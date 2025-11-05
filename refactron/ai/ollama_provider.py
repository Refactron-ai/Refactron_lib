"""Ollama provider for local AI models."""

import os

from refactron.ai.base import AIConfig, BaseAIProvider


class OllamaProvider(BaseAIProvider):
    """Ollama provider for local AI models (free, no API key needed)."""

    def __init__(self, config: AIConfig):
        """Initialize Ollama provider."""
        super().__init__(config)
        self.model = config.model or "codellama"
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        try:
            import requests

            self.requests = requests
        except ImportError:
            raise ImportError("requests package not installed. Install with: pip install requests")

        # Check if Ollama is running
        if not self._is_ollama_available():
            raise ConnectionError(
                f"Ollama not available at {self.base_url}. "
                "Make sure Ollama is running (visit https://ollama.ai)"
            )

    def _is_ollama_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            response = self.requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _call_api(self, prompt: str, system_prompt: str = "") -> str:
        """Call Ollama API with the given prompt."""
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            response = self.requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens,
                    },
                },
                timeout=self.config.timeout,
            )

            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                return f"Error calling Ollama API: {response.status_code} {response.text}"
        except Exception as e:
            return f"Error calling Ollama API: {str(e)}"

    def generate_docstring(self, code: str, context: str = "") -> str:
        """Generate docstring for code using Ollama."""
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
