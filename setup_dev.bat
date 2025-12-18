@echo off
REM Refactron Development Setup Script for Windows
REM This script automates the setup of the development environment

echo 🚀 Setting up Refactron development environment...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is required but not found.
    echo Please install Python 3.8 or higher and try again.
    exit /b 1
)

echo ✅ Python detected
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

echo.
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo ❌ Error: Failed to upgrade pip
    exit /b 1
)

REM Install the package in editable mode with dev dependencies
echo.
echo 📥 Installing Refactron in development mode...
python -m pip install -e ".[dev]" --quiet
if errorlevel 1 (
    echo ❌ Error: Failed to install Refactron in development mode
    exit /b 1
)

REM Install additional dev dependencies if requirements-dev.txt exists
if exist "requirements-dev.txt" (
    echo 📥 Installing additional development dependencies...
    python -m pip install -r requirements-dev.txt --quiet
    if errorlevel 1 (
        echo ❌ Error: Failed to install development dependencies
        exit /b 1
    )
)

REM Install pre-commit hooks
echo.
echo 🔧 Setting up pre-commit hooks...
where pre-commit >nul 2>&1
if errorlevel 1 (
    echo ⚠️  pre-commit not found. Installing...
    python -m pip install pre-commit --quiet
    if errorlevel 1 (
        echo ❌ Error: Failed to install pre-commit
        exit /b 1
    )
)
pre-commit install
if errorlevel 1 (
    echo ❌ Error: Failed to install pre-commit hooks
    exit /b 1
)
echo ✅ Pre-commit hooks installed

REM Verify installation
echo.
echo 🧪 Verifying installation...
python -c "import refactron; print('✅ Refactron imported successfully')" 2>nul
if errorlevel 1 (
    echo ❌ Error: Could not import refactron
    exit /b 1
)

REM Check CLI
echo.
echo 🔍 Checking CLI...
refactron --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: CLI not working
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('refactron --version') do set VERSION=%%i
    echo ✅ CLI working: %VERSION%
)

echo.
echo ✨ Development environment setup complete!
echo.
echo 📝 Next steps:
echo    1. Activate the virtual environment: venv\Scripts\activate
echo    2. Make your changes
echo    3. Run tests: pytest
echo    4. Format code: black refactron tests
echo    5. Check code quality: flake8 refactron
echo.
echo 💡 To activate the environment in the future, run:
echo    venv\Scripts\activate
echo.
echo Happy coding! 🚀
pause

