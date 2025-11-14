"""Comprehensive tests for the CLI interface."""

import os
import tempfile
from pathlib import Path

from click.testing import CliRunner

from refactron.cli import analyze, init, main, refactor, report


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_main_help(self):
        """Test main help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Refactron" in result.output
        assert "analyze" in result.output
        assert "refactor" in result.output

    def test_version(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output


class TestAnalyzeCommand:
    """Test the analyze command."""

    def test_analyze_help(self):
        """Test analyze help."""
        runner = CliRunner()
        result = runner.invoke(analyze, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output.lower()

    def test_analyze_single_file(self):
        """Test analyzing a single file."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def test_function(a, b, c, d, e, f):
    '''Function with too many parameters.'''
    return a + b + c + d + e + f
"""
            )
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            assert result.exit_code == 0
            assert "Analysis Summary" in result.output or "Files Analyzed" in result.output
        finally:
            os.unlink(temp_path)

    def test_analyze_with_summary_flag(self):
        """Test analyze with --summary flag."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def simple(): pass")
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path, "--summary"])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_analyze_with_detailed_flag(self):
        """Test analyze with --detailed flag."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def simple(): pass")
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path, "--detailed"])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_analyze_nonexistent_file(self):
        """Test analyzing a nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(analyze, ["/nonexistent/file.py"])
        assert result.exit_code != 0

    def test_analyze_directory(self):
        """Test analyzing a directory."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def test(): pass")

            result = runner.invoke(analyze, [tmpdir])
            assert result.exit_code == 0

    def test_analyze_detects_issues(self):
        """Test that analyze actually detects issues."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def bad_function(a, b, c, d, e, f, g):
    if True:
        if True:
            if True:
                if True:
                    return eval(a)
"""
            )
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            # Should detect multiple issues
            assert "Issues" in result.output or "Total" in result.output
        finally:
            os.unlink(temp_path)

    def test_analyze_with_config(self):
        """Test analyze with config file."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file
            config_path = Path(tmpdir) / ".refactron.yaml"
            config_path.write_text(
                """
enabled_analyzers:
  - complexity
max_function_complexity: 5
"""
            )

            # Create test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def test(): pass")

            result = runner.invoke(analyze, [str(test_file), "-c", str(config_path)])
            assert result.exit_code == 0


class TestRefactorCommand:
    """Test the refactor command."""

    def test_refactor_help(self):
        """Test refactor help."""
        runner = CliRunner()
        result = runner.invoke(refactor, ["--help"])
        assert result.exit_code == 0
        assert "refactor" in result.output.lower()

    def test_refactor_preview_mode(self):
        """Test refactor in preview mode."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def calculate_discount(price):
    if price > 1000:
        return price * 0.15
    return 0
"""
            )
            temp_path = f.name

        try:
            result = runner.invoke(refactor, [temp_path, "--preview"])
            assert result.exit_code == 0
            assert "Refactoring" in result.output or "Operations" in result.output
        finally:
            os.unlink(temp_path)

    def test_refactor_with_types_filter(self):
        """Test refactor with specific types."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass")
            temp_path = f.name

        try:
            result = runner.invoke(refactor, [temp_path, "--preview", "-t", "extract_constant"])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_refactor_nonexistent_file(self):
        """Test refactoring a nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(refactor, ["/nonexistent/file.py"])
        assert result.exit_code != 0


class TestReportCommand:
    """Test the report command."""

    def test_report_help(self):
        """Test report help."""
        runner = CliRunner()
        result = runner.invoke(report, ["--help"])
        assert result.exit_code == 0
        assert "report" in result.output.lower()

    def test_report_text_format(self):
        """Test report with text format."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass")
            temp_path = f.name

        try:
            result = runner.invoke(report, [temp_path, "-f", "text"])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_report_json_format(self):
        """Test report with JSON format."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass")
            temp_path = f.name

        try:
            result = runner.invoke(report, [temp_path, "-f", "json"])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_report_with_output_file(self):
        """Test report with output file."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def test(): pass")

            output_file = Path(tmpdir) / "report.txt"

            result = runner.invoke(report, [str(test_file), "-o", str(output_file)])
            assert result.exit_code == 0
            assert output_file.exists()
            assert output_file.stat().st_size > 0

    def test_report_nonexistent_file(self):
        """Test report on nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(report, ["/nonexistent/file.py"])
        assert result.exit_code != 0


class TestInitCommand:
    """Test the init command."""

    def test_init_help(self):
        """Test init help."""
        runner = CliRunner()
        result = runner.invoke(init, ["--help"])
        assert result.exit_code == 0

    def test_init_creates_config(self):
        """Test that init creates config file."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(init)
                assert result.exit_code == 0

                config_path = Path(tmpdir) / ".refactron.yaml"
                assert config_path.exists()

                content = config_path.read_text()
                assert "enabled_analyzers" in content
                assert "enabled_refactorers" in content
            finally:
                os.chdir(original_dir)

    def test_init_doesnt_overwrite_without_confirm(self):
        """Test that init doesn't overwrite existing config without confirmation."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Create existing config
                config_path = Path(tmpdir) / ".refactron.yaml"
                config_path.write_text("existing: config")

                # Try to init without confirming
                _result = runner.invoke(init, input="n\n")  # noqa: F841

                # Should still have original content
                assert "existing: config" in config_path.read_text()
            finally:
                os.chdir(original_dir)


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_invalid_command(self):
        """Test invalid command."""
        runner = CliRunner()
        result = runner.invoke(main, ["invalid_command"])
        assert result.exit_code != 0

    def test_analyze_empty_file(self):
        """Test analyzing an empty file."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            # Should handle gracefully
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_analyze_binary_file(self):
        """Test analyzing a binary file."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pyc", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            # Should handle gracefully or skip
            assert result.exit_code in [0, 1]
        finally:
            os.unlink(temp_path)

    def test_analyze_syntax_error_file(self):
        """Test analyzing a file with syntax errors."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def broken function(:")
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            # Should handle gracefully
            assert result.exit_code in [0, 1]
        finally:
            os.unlink(temp_path)


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_full_workflow(self):
        """Test complete workflow: init, analyze, refactor, report."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)

                # 1. Init
                result = runner.invoke(init)
                assert result.exit_code == 0

                # 2. Create test file
                test_file = Path(tmpdir) / "test.py"
                test_file.write_text(
                    """
def calculate(price):
    if price > 1000:
        return price * 0.15
    return 0
"""
                )

                # 3. Analyze
                result = runner.invoke(analyze, [str(test_file)])
                assert result.exit_code == 0

                # 4. Refactor
                result = runner.invoke(refactor, [str(test_file), "--preview"])
                assert result.exit_code == 0

                # 5. Report
                output_file = Path(tmpdir) / "report.txt"
                result = runner.invoke(report, [str(test_file), "-o", str(output_file)])
                assert result.exit_code == 0
                assert output_file.exists()

            finally:
                os.chdir(original_dir)

    def test_analyze_with_all_analyzers(self):
        """Test analyze with all analyzers enabled."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import os
import json

def process(data):
    # Some issues but no critical ones
    if True:
        result = data * 2
    return result

def unused():
    pass
"""
            )
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            assert result.exit_code == 0
            # Should detect multiple types of issues
        finally:
            os.unlink(temp_path)
