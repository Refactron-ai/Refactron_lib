"""Tests for AI service and providers."""

import pytest

from refactron.ai import AIConfig, AIProvider, AIService, create_ai_service


class TestAIConfig:
    """Test AI configuration."""

    def test_default_config(self):
        """Test default AI configuration."""
        config = AIConfig()
        assert config.enabled is False
        assert config.provider == AIProvider.OPENAI
        assert config.api_key is None
        assert config.temperature == 0.7
        assert config.max_tokens == 2000

    def test_custom_config(self):
        """Test custom AI configuration."""
        config = AIConfig(
            enabled=True,
            provider=AIProvider.ANTHROPIC,
            api_key="test-key",
            model="test-model",
            temperature=0.5,
            max_tokens=1000,
        )
        assert config.enabled is True
        assert config.provider == AIProvider.ANTHROPIC
        assert config.api_key == "test-key"
        assert config.model == "test-model"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000


class TestAIService:
    """Test AI service."""

    def test_disabled_service(self):
        """Test that disabled service raises errors."""
        service = AIService()
        assert not service.is_enabled()

        with pytest.raises(RuntimeError, match="AI features not enabled"):
            service.explain_code("def foo(): pass")

        with pytest.raises(RuntimeError, match="AI features not enabled"):
            service.generate_docstring("def foo(): pass")

        with pytest.raises(RuntimeError, match="AI features not enabled"):
            service.suggest_improvements("def foo(): pass", [])

        with pytest.raises(RuntimeError, match="AI features not enabled"):
            service.optimize_code("def foo(): pass")

        with pytest.raises(RuntimeError, match="AI features not enabled"):
            service.generate_refactoring_suggestion("def foo(): pass", "complexity")

    def test_unsupported_provider(self):
        """Test that unsupported provider raises error."""

        class UnsupportedProvider:
            pass

        config = AIConfig(enabled=True)
        config.provider = UnsupportedProvider()

        with pytest.raises(ValueError, match="Unsupported AI provider"):
            AIService(config)


class TestAIServiceFactory:
    """Test AI service factory."""

    def test_create_service_openai(self):
        """Test creating OpenAI service (without actual API key)."""
        # This will fail without API key, but tests the factory
        try:
            service = create_ai_service(provider="openai", api_key="test-key")
            assert service.config.provider == AIProvider.OPENAI
            assert service.config.enabled is True
        except ImportError:
            # openai package not installed
            pytest.skip("openai package not installed")
        except ValueError:
            # Invalid API key is expected
            pass

    def test_create_service_anthropic(self):
        """Test creating Anthropic service (without actual API key)."""
        try:
            service = create_ai_service(provider="anthropic", api_key="test-key")
            assert service.config.provider == AIProvider.ANTHROPIC
            assert service.config.enabled is True
        except ImportError:
            # anthropic package not installed
            pytest.skip("anthropic package not installed")
        except ValueError:
            # Invalid API key is expected
            pass

    def test_create_service_ollama(self):
        """Test creating Ollama service (without actual server)."""
        try:
            service = create_ai_service(provider="ollama", model="codellama")
            assert service.config.provider == AIProvider.OLLAMA
            assert service.config.enabled is True
        except (ImportError, ConnectionError):
            # requests not installed or Ollama not running
            pytest.skip("requests package not installed or Ollama not running")


class TestAIProviders:
    """Test individual AI providers."""

    def test_openai_provider_missing_key(self):
        """Test OpenAI provider without API key."""
        from refactron.ai.openai_provider import OpenAIProvider

        config = AIConfig(enabled=True, provider=AIProvider.OPENAI)

        with pytest.raises(ValueError, match="OpenAI API key required"):
            OpenAIProvider(config)

    def test_anthropic_provider_missing_key(self):
        """Test Anthropic provider without API key."""
        from refactron.ai.anthropic_provider import AnthropicProvider

        config = AIConfig(enabled=True, provider=AIProvider.ANTHROPIC)

        with pytest.raises(ValueError, match="Anthropic API key required"):
            AnthropicProvider(config)

    def test_ollama_provider_not_available(self):
        """Test Ollama provider when server is not running."""
        from refactron.ai.ollama_provider import OllamaProvider

        config = AIConfig(enabled=True, provider=AIProvider.OLLAMA)

        try:
            OllamaProvider(config)
        except ConnectionError as e:
            assert "Ollama not available" in str(e)
        except ImportError:
            pytest.skip("requests package not installed")
