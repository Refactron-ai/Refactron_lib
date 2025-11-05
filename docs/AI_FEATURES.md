# 🤖 AI-Powered Features Guide

Refactron now includes **optional AI-powered features** for enhanced code analysis, documentation, and refactoring suggestions. These features support multiple AI providers and are completely opt-in.

## 🎯 Overview

The AI features provide:
- **Code Explanation** - Understand what your code does
- **Improvement Suggestions** - Get AI recommendations based on detected issues
- **Optimization Tips** - Performance and efficiency improvements
- **Documentation Generation** - Auto-generate docstrings and documentation
- **Refactoring Guidance** - Step-by-step refactoring recommendations

## 🚀 Quick Start

### Installation

AI features require additional dependencies. Install them with:

```bash
# Install all AI dependencies
pip install refactron[ai]

# Or install specific providers only
pip install openai         # For OpenAI/GPT
pip install anthropic      # For Anthropic/Claude
pip install requests       # For Ollama (local)
```

### Basic Usage

```python
from refactron import Refactron, AIConfig, AIProvider

# Configure AI (using OpenAI as example)
ai_config = AIConfig(
    enabled=True,
    provider=AIProvider.OPENAI,
    api_key="your-api-key"  # Or set OPENAI_API_KEY env var
)

# Initialize Refactron with AI
refactron = Refactron(ai_config=ai_config)

# Get AI suggestions
suggestions = refactron.get_ai_suggestions("mycode.py")
print(suggestions['explanation'])
print(suggestions['improvements'])
print(suggestions['optimizations'])

# Generate documentation
docs = refactron.generate_documentation("mycode.py")
print(docs)

# Get refactoring suggestions
refactoring = refactron.get_refactoring_suggestions("mycode.py", "complexity")
print(refactoring)
```

## 🔌 Supported Providers

### 1. OpenAI (GPT Models)

**Best for:** High-quality suggestions, wide language support
**Cost:** Paid API (user provides key)

```python
from refactron import AIConfig, AIProvider

ai_config = AIConfig(
    enabled=True,
    provider=AIProvider.OPENAI,
    api_key="sk-...",  # Or set OPENAI_API_KEY env var
    model="gpt-4o-mini",  # or gpt-4, gpt-3.5-turbo
    temperature=0.7,
    max_tokens=2000
)
```

**Setup:**
1. Get API key from https://platform.openai.com/api-keys
2. Set environment variable: `export OPENAI_API_KEY=sk-...`
3. Or pass directly in config

**Models:**
- `gpt-4o-mini` (recommended, fast and cheap)
- `gpt-4` (most capable)
- `gpt-3.5-turbo` (fastest)

### 2. Anthropic (Claude Models)

**Best for:** Long context, detailed explanations
**Cost:** Paid API (user provides key)

```python
ai_config = AIConfig(
    enabled=True,
    provider=AIProvider.ANTHROPIC,
    api_key="sk-ant-...",  # Or set ANTHROPIC_API_KEY env var
    model="claude-3-5-sonnet-20241022"
)
```

**Setup:**
1. Get API key from https://console.anthropic.com/
2. Set environment variable: `export ANTHROPIC_API_KEY=sk-ant-...`
3. Or pass directly in config

**Models:**
- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-opus-20240229` (most capable)
- `claude-3-haiku-20240307` (fastest)

### 3. Ollama (Local Models)

**Best for:** Privacy, offline use, no cost
**Cost:** FREE (runs locally)

```python
ai_config = AIConfig(
    enabled=True,
    provider=AIProvider.OLLAMA,
    model="codellama"  # or deepseek-coder, qwen2.5-coder
)
```

**Setup:**
1. Install Ollama from https://ollama.ai
2. Pull a code model: `ollama pull codellama`
3. Start Ollama (runs automatically after install)
4. No API key needed!

**Recommended Models:**
- `codellama` - Code Llama by Meta (7B, 13B, 34B)
- `deepseek-coder` - DeepSeek Coder (6.7B, 33B)
- `qwen2.5-coder` - Qwen 2.5 Coder (0.5B to 32B)
- `starcoder2` - StarCoder2 (3B, 7B, 15B)

## 📖 API Reference

### AIConfig

Configuration for AI features.

```python
from refactron import AIConfig, AIProvider

config = AIConfig(
    enabled=True,           # Enable AI features
    provider=AIProvider.OPENAI,  # AI provider
    api_key="...",         # API key (optional for Ollama)
    model="gpt-4o-mini",   # Model name (optional)
    temperature=0.7,        # Creativity (0.0-1.0)
    max_tokens=2000,       # Max response length
    timeout=30             # Request timeout in seconds
)
```

### AIService

Direct AI service for advanced use cases.

```python
from refactron import create_ai_service

# Factory function for quick setup
service = create_ai_service(
    provider="openai",
    api_key="sk-...",
    model="gpt-4o-mini"
)

# Use service directly
docstring = service.generate_docstring(code)
explanation = service.explain_code(code)
improvements = service.suggest_improvements(code, issues)
optimizations = service.optimize_code(code)
refactoring = service.generate_refactoring_suggestion(code, issue_type)
```

### Refactron Methods

#### get_ai_suggestions(target)

Get comprehensive AI suggestions for a file.

```python
suggestions = refactron.get_ai_suggestions("mycode.py")

# Returns dict with:
# - explanation: What the code does
# - improvements: Suggestions based on detected issues
# - optimizations: Performance and efficiency tips
```

#### generate_documentation(target, function_name="")

Generate AI-powered documentation.

```python
# Document entire file
docs = refactron.generate_documentation("mycode.py")

# Document specific function
docs = refactron.generate_documentation("mycode.py", "my_function")
```

#### get_refactoring_suggestions(target, issue_type="general")

Get specific refactoring recommendations.

```python
# General refactoring
refactoring = refactron.get_refactoring_suggestions("mycode.py")

# Specific issue types
refactoring = refactron.get_refactoring_suggestions("mycode.py", "complexity")
refactoring = refactron.get_refactoring_suggestions("mycode.py", "code_smell")
refactoring = refactron.get_refactoring_suggestions("mycode.py", "security")
```

## 💡 Examples

### Example 1: Basic Analysis

```python
from refactron import Refactron, create_ai_service

# Create AI service
ai_config = create_ai_service(
    provider="ollama",  # Free local model
    model="codellama"
).config

# Analyze code
refactron = Refactron(ai_config=ai_config)
suggestions = refactron.get_ai_suggestions("mycode.py")

print(f"Explanation: {suggestions['explanation']}")
print(f"Improvements: {suggestions['improvements']}")
```

### Example 2: Documentation Generation

```python
from refactron import Refactron, AIConfig, AIProvider

ai_config = AIConfig(
    enabled=True,
    provider=AIProvider.OPENAI,
    model="gpt-4o-mini"
)

refactron = Refactron(ai_config=ai_config)

# Generate docstring
code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""

with open("fib.py", "w") as f:
    f.write(code)

docs = refactron.generate_documentation("fib.py", "calculate_fibonacci")
print(docs)
```

### Example 3: Optimization Suggestions

```python
# Get optimization suggestions
suggestions = refactron.get_ai_suggestions("slow_code.py")
print(suggestions['optimizations'])
# Output includes:
# - Performance improvements
# - Memory efficiency tips
# - Readability enhancements
# - Best practices
```

## 🎛️ Configuration

### Environment Variables

Set API keys via environment variables for security:

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Ollama (custom URL if needed)
export OLLAMA_BASE_URL=http://localhost:11434
```

### Configuration File

Create `.refactron-ai.yaml`:

```yaml
ai:
  enabled: true
  provider: openai  # or anthropic, ollama
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
```

## 💰 Cost Comparison

| Provider | Cost per 1M tokens | Speed | Privacy |
|----------|-------------------|-------|---------|
| **Ollama** | **FREE** | Fast | ✅ Local |
| OpenAI GPT-4o-mini | ~$0.15 | Fast | ☁️ Cloud |
| OpenAI GPT-4 | ~$30 | Medium | ☁️ Cloud |
| Anthropic Claude 3.5 Sonnet | ~$3 | Fast | ☁️ Cloud |

**Recommendation:** Start with Ollama (free, local) for testing, use cloud APIs for production if needed.

## 🔒 Privacy & Security

### Local Models (Ollama)
- ✅ Code never leaves your machine
- ✅ No API keys needed
- ✅ Works offline
- ✅ No usage limits

### Cloud APIs (OpenAI, Anthropic)
- ⚠️ Code sent to provider
- ⚠️ API key required
- ⚠️ Internet required
- ⚠️ Usage costs apply

**Best Practice:** Use Ollama for sensitive code, cloud APIs for public/open-source projects.

## 🐛 Troubleshooting

### "AI features not enabled"
```python
# Make sure to pass ai_config when initializing Refactron
ai_config = AIConfig(enabled=True, ...)
refactron = Refactron(ai_config=ai_config)
```

### "OpenAI API key required"
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### "Ollama not available"
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull a model
ollama pull codellama

# Start Ollama (usually auto-starts)
ollama serve
```

### Import errors
```bash
# Install AI dependencies
pip install refactron[ai]

# Or install specific provider
pip install openai anthropic requests
```

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic API Documentation](https://docs.anthropic.com)
- [Ollama Models](https://ollama.ai/library)
- [Refactron Examples](../examples/ai_features_example.py)

## 🤝 Contributing

Want to add support for more AI providers? See our [Contributing Guide](../CONTRIBUTING.md)!

---

**Note:** AI features are completely optional. All core Refactron functionality works without AI configuration.
