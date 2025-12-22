#!/bin/bash

# Refactron Development Setup Script
# This script automates the setup of the development environment

set -e  # Exit on any error

echo "🚀 Setting up Refactron development environment..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not found."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check Python version (must be 3.8+)
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo "❌ Error: Python 3.8 or higher is required. Found Python $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install the package in editable mode with dev dependencies
echo ""
echo "📥 Installing Refactron in development mode..."
pip install -e ".[dev]" --quiet

# Install additional (non-core) dev dependencies if requirements-dev.txt exists
# NOTE:
#   - Core development tools (pytest, black, mypy, flake8, isort, etc.) are installed
#     via the [dev] extra in pyproject.toml (see the pip install -e ".[dev]" above).
#   - To avoid redundant installations and version conflicts, we only use
#     requirements-dev.txt for *extra* tools such as documentation dependencies.
if [ -f "requirements-dev.txt" ]; then
    echo "📥 Installing additional documentation/development dependencies from requirements-dev.txt..."

    # Extract Sphinx-related requirements (e.g., sphinx, sphinx-rtd-theme) from
    # requirements-dev.txt and install only those. This avoids re-installing tools
    # that are already provided by the [dev] extra.
    DOC_REQUIREMENTS=$(grep -E '^[[:space:]]*sphinx' requirements-dev.txt || true)

    if [ -n "$DOC_REQUIREMENTS" ]; then
        echo "$DOC_REQUIREMENTS" | xargs -n1 pip install --quiet
    else
        echo "ℹ️  No additional documentation dependencies detected in requirements-dev.txt; skipping."
    fi
fi

# Install pre-commit hooks
echo ""
echo "🔧 Setting up pre-commit hooks..."
pre-commit install
echo "✅ Pre-commit hooks installed"

# Verify installation
echo ""
echo "🧪 Verifying installation..."
# Use python3 for consistency (venv should have it, but python3 is more reliable)
if python3 -c "import refactron; print('✅ Refactron imported successfully')" 2>/dev/null; then
    echo "✅ Installation verified"
else
    echo "❌ Error: Could not import refactron"
    exit 1
fi

# Check CLI
echo ""
echo "🔍 Checking CLI..."
if refactron --version &> /dev/null; then
    VERSION=$(refactron --version)
    echo "✅ CLI working: $VERSION"
else
    echo "❌ Error: CLI not working"
    exit 1
fi

# Run tests to verify everything works
echo ""
echo "🧪 Running tests to verify setup..."
if pytest --version &> /dev/null; then
    if ! pytest tests/ -v --tb=short -x; then
        echo ""
        echo "⚠️  Some tests failed, but setup is complete."
        echo "You can investigate test failures later."
    fi
else
    echo "⚠️  pytest not found. Setup complete, but tests couldn't run."
fi

echo ""
echo "✨ Development environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Activate the virtual environment: source venv/bin/activate"
echo "   2. Make your changes"
echo "   3. Run tests: pytest"
echo "   4. Format code: black refactron tests"
echo "   5. Check code quality: flake8 refactron"
echo ""
echo "💡 To activate the environment in the future, run:"
echo "   source venv/bin/activate"
echo ""
echo "Happy coding! 🚀"

