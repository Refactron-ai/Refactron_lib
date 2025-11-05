"""
AI-powered code analysis and suggestions module.

Supports multiple AI providers:
- OpenAI (GPT models) - requires API key
- Anthropic (Claude models) - requires API key
- Ollama (local models) - free, no API key needed
"""

from refactron.ai.base import AIConfig, AIProvider, BaseAIProvider
from refactron.ai.service import AIService, create_ai_service

__all__ = [
    "AIService",
    "AIConfig",
    "AIProvider",
    "BaseAIProvider",
    "create_ai_service",
]
