"""
Example demonstrating AI-powered features in Refactron.

This example shows how to use AI for:
1. Code explanation
2. Improvement suggestions
3. Optimization recommendations
4. Documentation generation
5. Refactoring suggestions
"""

from refactron import AIConfig, AIProvider, Refactron


def example_with_openai():
    """Example using OpenAI (requires API key)."""
    print("=" * 60)
    print("Example 1: Using OpenAI GPT Models")
    print("=" * 60)

    # Configure AI with OpenAI
    ai_config = AIConfig(
        enabled=True,
        provider=AIProvider.OPENAI,
        api_key="your-openai-api-key",  # Or set OPENAI_API_KEY env var
        model="gpt-4o-mini",
        temperature=0.7,
    )

    # Initialize Refactron with AI
    refactron = Refactron(ai_config=ai_config)

    # Analyze sample code
    sample_code = """
def calc(a, b, op):
    if op == "add":
        return a + b
    elif op == "sub":
        return a - b
    elif op == "mul":
        return a * b
    elif op == "div":
        return a / b
"""

    # Save sample to file
    with open("/tmp/sample.py", "w") as f:
        f.write(sample_code)

    # Get AI suggestions
    print("\n1. Getting AI suggestions...")
    suggestions = refactron.get_ai_suggestions("/tmp/sample.py")
    print(f"\nExplanation:\n{suggestions['explanation']}")
    print(f"\nImprovements:\n{suggestions['improvements']}")
    print(f"\nOptimizations:\n{suggestions['optimizations']}")

    # Generate documentation
    print("\n2. Generating documentation...")
    docs = refactron.generate_documentation("/tmp/sample.py")
    print(f"\nGenerated Docs:\n{docs}")

    # Get refactoring suggestions
    print("\n3. Getting refactoring suggestions...")
    refactoring = refactron.get_refactoring_suggestions("/tmp/sample.py", "complexity")
    print(f"\nRefactoring:\n{refactoring}")


def example_with_anthropic():
    """Example using Anthropic Claude (requires API key)."""
    print("\n" + "=" * 60)
    print("Example 2: Using Anthropic Claude")
    print("=" * 60)

    ai_config = AIConfig(
        enabled=True,
        provider=AIProvider.ANTHROPIC,
        api_key="your-anthropic-api-key",  # Or set ANTHROPIC_API_KEY env var
        model="claude-3-5-sonnet-20241022",
    )

    refactron = Refactron(ai_config=ai_config)

    sample_code = """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            if item % 2 == 0:
                result.append(item * 2)
    return result
"""

    with open("/tmp/sample2.py", "w") as f:
        f.write(sample_code)

    suggestions = refactron.get_ai_suggestions("/tmp/sample2.py")
    print(f"\nClaude's suggestions:\n{suggestions['improvements']}")


def example_with_ollama():
    """Example using Ollama (free, local, no API key needed)."""
    print("\n" + "=" * 60)
    print("Example 3: Using Ollama (Local, Free)")
    print("=" * 60)

    # No API key needed for Ollama!
    ai_config = AIConfig(
        enabled=True,
        provider=AIProvider.OLLAMA,
        model="codellama",  # Or deepseek-coder, qwen2.5-coder, etc.
    )

    refactron = Refactron(ai_config=ai_config)

    sample_code = """
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)
"""

    with open("/tmp/sample3.py", "w") as f:
        f.write(sample_code)

    print("\n1. Explaining code with local model...")
    suggestions = refactron.get_ai_suggestions("/tmp/sample3.py")
    print(f"\nExplanation:\n{suggestions['explanation']}")

    print("\n2. Suggesting optimizations...")
    print(f"\nOptimizations:\n{suggestions['optimizations']}")


def example_with_factory():
    """Example using the factory function for quick setup."""
    print("\n" + "=" * 60)
    print("Example 4: Using Factory Function")
    print("=" * 60)

    from refactron import create_ai_service

    # Quick setup with factory
    ai_service = create_ai_service(
        provider="ollama",  # or 'openai', 'anthropic'
        model="codellama",
    )

    code = "def add(x, y): return x + y"

    print("\nGenerating docstring...")
    docstring = ai_service.generate_docstring(code)
    print(f"Docstring: {docstring}")

    print("\nExplaining code...")
    explanation = ai_service.explain_code(code)
    print(f"Explanation: {explanation}")


def example_error_handling():
    """Example showing error handling when AI is not configured."""
    print("\n" + "=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)

    # Create Refactron without AI config
    refactron = Refactron()

    try:
        refactron.get_ai_suggestions("/tmp/sample.py")
    except RuntimeError as e:
        print(f"\nExpected error: {e}")
        print("✓ Proper error handling when AI is not configured")


def main():
    """Run all examples."""
    print("\n🤖 Refactron AI Features Examples\n")

    # Note: These examples require API keys or Ollama installation
    # Uncomment the examples you want to try:

    # example_with_openai()  # Requires OPENAI_API_KEY
    # example_with_anthropic()  # Requires ANTHROPIC_API_KEY
    # example_with_ollama()  # Requires Ollama running locally
    # example_with_factory()
    example_error_handling()

    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60)
    print("\nTo use AI features:")
    print("1. For OpenAI: Set OPENAI_API_KEY env var")
    print("2. For Anthropic: Set ANTHROPIC_API_KEY env var")
    print("3. For Ollama: Install from https://ollama.ai")
    print("\nThen uncomment the relevant examples above.")


if __name__ == "__main__":
    main()
