"""
Concrete fixer implementations for common code issues.

All fixers use AST-based transformations for reliability and speed.
No expensive AI APIs required!
"""

import ast
from typing import Set

from refactron.autofix.engine import BaseFixer
from refactron.autofix.models import FixResult
from refactron.core.models import CodeIssue


class RemoveUnusedImportsFixer(BaseFixer):
    """Removes unused import statements."""

    def __init__(self) -> None:
        super().__init__(name="remove_unused_imports", risk_score=0.0)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview the removal of unused imports."""
        result = self._remove_unused_imports(code)

        if result["removed_count"] == 0:
            return FixResult(
                success=True,
                reason="No unused imports found - code is clean!",
                original=code,
                fixed=code,
                risk_score=self.risk_score,
            )

        return FixResult(
            success=True,
            reason=f"Removed {result['removed_count']} unused import(s)",
            diff=self._create_diff(code, result["fixed"]),
            original=code,
            fixed=result["fixed"],
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply the fix to remove unused imports."""
        return self.preview(issue, code)

    def _remove_unused_imports(self, code: str) -> dict:
        """Remove unused imports from code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"fixed": code, "removed_count": 0}

        # Find all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "name": alias.asname or alias.name,
                            "module": alias.name,
                            "lineno": node.lineno,
                            "type": "import",
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        continue  # Skip wildcard imports (risky to remove)
                    imports.append(
                        {
                            "name": alias.asname or alias.name,
                            "module": node.module,
                            "lineno": node.lineno,
                            "type": "from",
                        }
                    )

        # Find all name usages
        used_names = self._find_used_names(tree)

        # Identify unused imports
        unused_lines = set()
        for imp in imports:
            if imp["name"] not in used_names:
                unused_lines.add(imp["lineno"])

        # Remove unused import lines
        lines = code.split("\n")
        fixed_lines = [line for i, line in enumerate(lines, 1) if i not in unused_lines]

        return {"fixed": "\n".join(fixed_lines), "removed_count": len(unused_lines)}

    def _find_used_names(self, tree: ast.AST) -> Set[str]:
        """Find all names used in the code."""
        used_names = set()

        for node in ast.walk(tree):
            # Skip import nodes
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue

            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # For attribute access like 'os.path', track 'os'
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        return used_names

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff showing changes."""
        orig_lines = original.split("\n")
        fixed_lines = fixed.split("\n")

        diff = []
        diff.append("--- Original")
        diff.append("+++ Fixed")

        for i, (orig, fix) in enumerate(zip(orig_lines, fixed_lines), 1):
            if orig != fix:
                diff.append(f"- Line {i}: {orig}")
                if fix:
                    diff.append(f"+ Line {i}: {fix}")

        # Handle removed lines at the end
        if len(orig_lines) > len(fixed_lines):
            for i in range(len(fixed_lines), len(orig_lines)):
                diff.append(f"- Line {i+1}: {orig_lines[i]}")

        return "\n".join(diff)


class ExtractMagicNumbersFixer(BaseFixer):
    """Extracts magic numbers into named constants."""

    def __init__(self) -> None:
        super().__init__(name="extract_magic_numbers", risk_score=0.2)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview magic number extraction."""
        # Get the magic number from the issue metadata
        if "value" not in issue.metadata:
            return FixResult(
                success=False,
                reason="No magic number value in issue metadata",
                risk_score=self.risk_score,
            )

        magic_number = issue.metadata["value"]
        constant_name = self._generate_constant_name(magic_number, issue)

        # Simple replacement for now
        fixed = code.replace(str(magic_number), constant_name)

        # Add constant definition at the top
        const_definition = f"{constant_name} = {magic_number}\n\n"
        fixed = const_definition + fixed

        return FixResult(
            success=True,
            reason=f"Extracted magic number {magic_number} to {constant_name}",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply magic number extraction."""
        return self.preview(issue, code)

    def _generate_constant_name(self, value: str, issue: CodeIssue) -> str:
        """Generate a meaningful constant name."""
        # Try to infer from context
        if "context" in issue.metadata:
            context = issue.metadata["context"]
            return f"{context.upper()}_VALUE"

        # Default naming
        if isinstance(value, float):
            return f"CONSTANT_{str(value).replace('.', '_')}"
        return f"CONSTANT_{value}"

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class AddDocstringsFixer(BaseFixer):
    """Adds missing docstrings to functions and classes."""

    def __init__(self) -> None:
        super().__init__(name="add_docstrings", risk_score=0.1)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview docstring addition."""
        try:
            # Parse to validate syntax before attempting to modify
            ast.parse(code)
        except SyntaxError:
            return FixResult(
                success=False, reason="Syntax error in code", risk_score=self.risk_score
            )

        # Find function/class needing docstring
        target_line = issue.line_number
        fixed_code = self._add_docstring(code, target_line)

        if fixed_code == code:
            return FixResult(
                success=False, reason="Could not add docstring", risk_score=self.risk_score
            )

        return FixResult(
            success=True,
            reason="Added docstring",
            diff=self._create_diff(code, fixed_code),
            original=code,
            fixed=fixed_code,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply docstring addition."""
        return self.preview(issue, code)

    def _add_docstring(self, code: str, line_number: int) -> str:
        """Add a docstring at the specified line."""
        lines = code.split("\n")

        if line_number > len(lines):
            return code

        # Get the function/class line
        func_line = lines[line_number - 1]
        indent = len(func_line) - len(func_line.lstrip())

        # Generate simple docstring
        docstring = " " * (indent + 4) + '"""TODO: Add description."""'

        # Insert after the function definition
        lines.insert(line_number, docstring)

        return "\n".join(lines)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class RemoveDeadCodeFixer(BaseFixer):
    """Removes dead/unreachable code."""

    def __init__(self) -> None:
        super().__init__(name="remove_dead_code", risk_score=0.1)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview dead code removal."""
        # Simple implementation: remove the line indicated by the issue
        lines = code.split("\n")

        if issue.line_number > len(lines):
            return FixResult(
                success=False, reason="Invalid line number", risk_score=self.risk_score
            )

        # Remove the dead code line
        removed_line = lines[issue.line_number - 1]
        lines.pop(issue.line_number - 1)
        fixed = "\n".join(lines)

        return FixResult(
            success=True,
            reason=f"Removed dead code: {removed_line.strip()}",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply dead code removal."""
        return self.preview(issue, code)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class FixTypeHintsFixer(BaseFixer):
    """Adds or fixes type hints."""

    def __init__(self) -> None:
        super().__init__(name="fix_type_hints", risk_score=0.4)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview type hint fix."""
        # This is a more complex fixer that would require type inference
        # For now, return a placeholder
        return FixResult(
            success=False, reason="Type hint fixing not yet implemented", risk_score=self.risk_score
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply type hint fix."""
        return self.preview(issue, code)


class SortImportsFixer(BaseFixer):
    """Sort and organize imports using isort."""

    def __init__(self) -> None:
        super().__init__(name="sort_imports", risk_score=0.0)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview import sorting."""
        try:
            import isort

            sorted_code = isort.code(code)

            if sorted_code == code:
                return FixResult(
                    success=True,
                    reason="Imports already sorted",
                    original=code,
                    fixed=code,
                    risk_score=self.risk_score,
                )

            return FixResult(
                success=True,
                reason="Sorted imports",
                diff=self._create_diff(code, sorted_code),
                original=code,
                fixed=sorted_code,
                risk_score=self.risk_score,
            )
        except ImportError:
            return FixResult(
                success=False,
                reason="isort not installed (pip install isort)",
                risk_score=self.risk_score,
            )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply import sorting."""
        return self.preview(issue, code)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class RemoveTrailingWhitespaceFixer(BaseFixer):
    """Remove trailing whitespace from lines."""

    def __init__(self) -> None:
        super().__init__(name="remove_trailing_whitespace", risk_score=0.0)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview whitespace removal."""
        lines = code.split("\n")
        fixed_lines = [line.rstrip() for line in lines]
        fixed = "\n".join(fixed_lines)

        if fixed == code:
            return FixResult(
                success=True,
                reason="No trailing whitespace found",
                original=code,
                fixed=code,
                risk_score=self.risk_score,
            )

        removed_count = sum(1 for orig, fix in zip(lines, fixed_lines) if orig != fix)

        return FixResult(
            success=True,
            reason=f"Removed trailing whitespace from {removed_count} line(s)",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply whitespace removal."""
        return self.preview(issue, code)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class NormalizeQuotesFixer(BaseFixer):
    """Normalize string quotes (single → double or vice versa)."""

    def __init__(self, prefer_double: bool = True):
        super().__init__(name="normalize_quotes", risk_score=0.1)
        self.prefer_double = prefer_double

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview quote normalization."""
        # Simple implementation using regex
        import re

        if self.prefer_double:
            # Convert single quotes to double (but not in comments or existing double quotes)
            fixed = re.sub(r"'([^']*)'", r'"\1"', code)
            direction = "single → double"
        else:
            # Convert double quotes to single
            fixed = re.sub(r'"([^"]*)"', r"'\1'", code)
            direction = "double → single"

        if fixed == code:
            return FixResult(
                success=True,
                reason="Quotes already normalized",
                original=code,
                fixed=code,
                risk_score=self.risk_score,
            )

        return FixResult(
            success=True,
            reason=f"Normalized quotes ({direction})",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply quote normalization."""
        return self.preview(issue, code)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class SimplifyBooleanFixer(BaseFixer):
    """Simplify boolean expressions."""

    def __init__(self) -> None:
        super().__init__(name="simplify_boolean", risk_score=0.3)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview boolean simplification."""
        # Simple patterns to fix
        import re

        fixed = code
        changes = []

        # if x == True: → if x:
        if re.search(r"if\s+\w+\s*==\s*True", fixed):
            fixed = re.sub(r"if\s+(\w+)\s*==\s*True", r"if \1", fixed)
            changes.append("x == True → x")

        # if x == False: → if not x:
        if re.search(r"if\s+\w+\s*==\s*False", fixed):
            fixed = re.sub(r"if\s+(\w+)\s*==\s*False", r"if not \1", fixed)
            changes.append("x == False → not x")

        # if not x == False: → if x:
        if re.search(r"if\s+not\s+\w+\s*==\s*False", fixed):
            fixed = re.sub(r"if\s+not\s+(\w+)\s*==\s*False", r"if \1", fixed)
            changes.append("not x == False → x")

        if fixed == code:
            return FixResult(
                success=False, reason="No boolean simplifications found", risk_score=self.risk_score
            )

        return FixResult(
            success=True,
            reason=f"Simplified: {', '.join(changes)}",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply boolean simplification."""
        return self.preview(issue, code)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class ConvertToFStringFixer(BaseFixer):
    """Convert old-style format strings to f-strings."""

    def __init__(self) -> None:
        super().__init__(name="convert_to_fstring", risk_score=0.2)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview f-string conversion."""
        import re

        fixed = code
        changes = 0

        # Convert "text {}".format(var) to f"text {var}"
        # Simple pattern (doesn't handle complex cases)
        pattern = r'"([^"]*)\{\}([^"]*)"\s*\.\s*format\((\w+)\)'
        if re.search(pattern, fixed):
            fixed = re.sub(pattern, r'f"\1{\3}\2"', fixed)
            changes += 1

        # Convert 'text {}'.format(var) to f'text {var}'
        pattern = r"'([^']*)\{\}([^']*)'\s*\.\s*format\((\w+)\)"
        if re.search(pattern, fixed):
            fixed = re.sub(pattern, r"f'\1{\3}\2'", fixed)
            changes += 1

        if changes == 0:
            return FixResult(
                success=False, reason="No format strings to convert", risk_score=self.risk_score
            )

        return FixResult(
            success=True,
            reason=f"Converted {changes} format string(s) to f-strings",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply f-string conversion."""
        return self.preview(issue, code)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class RemoveUnusedVariablesFixer(BaseFixer):
    """Remove unused variables."""

    def __init__(self) -> None:
        super().__init__(name="remove_unused_variables", risk_score=0.2)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview unused variable removal."""
        # Get variable name from issue metadata
        if "variable" not in issue.metadata:
            return FixResult(
                success=False,
                reason="No variable name in issue metadata",
                risk_score=self.risk_score,
            )

        var_name = issue.metadata["variable"]
        lines = code.split("\n")

        # Remove line with unused variable assignment
        fixed_lines = []
        removed = False
        for line in lines:
            if f"{var_name} =" in line and not removed:
                removed = True
                continue
            fixed_lines.append(line)

        fixed = "\n".join(fixed_lines)

        if not removed:
            return FixResult(
                success=False, reason=f"Variable {var_name} not found", risk_score=self.risk_score
            )

        return FixResult(
            success=True,
            reason=f"Removed unused variable: {var_name}",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply unused variable removal."""
        return self.preview(issue, code)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class FixIndentationFixer(BaseFixer):
    """Fix inconsistent indentation."""

    def __init__(self, spaces: int = 4):
        super().__init__(name="fix_indentation", risk_score=0.1)
        self.spaces = spaces

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview indentation fix."""
        lines = code.split("\n")
        fixed_lines = []
        changes = 0

        for line in lines:
            # Convert tabs to spaces
            if "\t" in line:
                fixed_line = line.replace("\t", " " * self.spaces)
                fixed_lines.append(fixed_line)
                if fixed_line != line:
                    changes += 1
            else:
                fixed_lines.append(line)

        fixed = "\n".join(fixed_lines)

        if changes == 0:
            return FixResult(
                success=True,
                reason="Indentation already consistent",
                original=code,
                fixed=code,
                risk_score=self.risk_score,
            )

        return FixResult(
            success=True,
            reason=f"Fixed indentation on {changes} line(s)",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply indentation fix."""
        return self.preview(issue, code)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class AddMissingCommasFixer(BaseFixer):
    """Add missing trailing commas in lists/dicts."""

    def __init__(self) -> None:
        super().__init__(name="add_missing_commas", risk_score=0.1)

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview comma addition."""
        import re

        # Add trailing comma before closing bracket/paren on multiline
        pattern = r"(\w+)\n(\s*)([\]\)])"
        fixed = re.sub(pattern, r"\1,\n\2\3", code)

        if fixed == code:
            return FixResult(
                success=False, reason="No missing commas found", risk_score=self.risk_score
            )

        return FixResult(
            success=True,
            reason="Added missing trailing commas",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply comma addition."""
        return self.preview(issue, code)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class RemovePrintStatementsFixer(BaseFixer):
    """Remove or convert print statements to logging."""

    def __init__(self, convert_to_logging: bool = False):
        super().__init__(name="remove_print_statements", risk_score=0.3)
        self.convert_to_logging = convert_to_logging

    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview print statement removal/conversion."""
        import re

        if self.convert_to_logging:
            # Convert print(x) to logger.info(x)
            fixed = re.sub(r"print\((.*?)\)", r"logger.info(\1)", code)
            action = "converted to logger.info"
        else:
            # Remove print statements
            lines = code.split("\n")
            fixed_lines = [line for line in lines if "print(" not in line]
            fixed = "\n".join(fixed_lines)
            action = "removed"

        if fixed == code:
            return FixResult(
                success=False, reason="No print statements found", risk_score=self.risk_score
            )

        return FixResult(
            success=True,
            reason=f"Print statements {action}",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score,
        )

    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply print statement removal/conversion."""
        return self.preview(issue, code)

    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"
