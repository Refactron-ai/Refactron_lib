"""
Concrete fixer implementations for common code issues.

All fixers use AST-based transformations for reliability and speed.
No expensive AI APIs required!
"""

import ast
import re
from typing import Set
from refactron.autofix.engine import BaseFixer
from refactron.autofix.models import FixResult
from refactron.core.models import CodeIssue


class RemoveUnusedImportsFixer(BaseFixer):
    """Removes unused import statements."""
    
    def __init__(self):
        super().__init__(name="remove_unused_imports", risk_score=0.0)
    
    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview the removal of unused imports."""
        result = self._remove_unused_imports(code)
        
        if result['removed_count'] == 0:
            return FixResult(
                success=True,
                reason="No unused imports found - code is clean!",
                original=code,
                fixed=code,
                risk_score=self.risk_score
            )
        
        return FixResult(
            success=True,
            reason=f"Removed {result['removed_count']} unused import(s)",
            diff=self._create_diff(code, result['fixed']),
            original=code,
            fixed=result['fixed'],
            risk_score=self.risk_score
        )
    
    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply the fix to remove unused imports."""
        return self.preview(issue, code)
    
    def _remove_unused_imports(self, code: str) -> dict:
        """Remove unused imports from code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {'fixed': code, 'removed_count': 0}
        
        # Find all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'name': alias.asname or alias.name,
                        'module': alias.name,
                        'lineno': node.lineno,
                        'type': 'import'
                    })
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        continue  # Skip wildcard imports (risky to remove)
                    imports.append({
                        'name': alias.asname or alias.name,
                        'module': node.module,
                        'lineno': node.lineno,
                        'type': 'from'
                    })
        
        # Find all name usages
        used_names = self._find_used_names(tree)
        
        # Identify unused imports
        unused_lines = set()
        for imp in imports:
            if imp['name'] not in used_names:
                unused_lines.add(imp['lineno'])
        
        # Remove unused import lines
        lines = code.split('\n')
        fixed_lines = [
            line for i, line in enumerate(lines, 1)
            if i not in unused_lines
        ]
        
        return {
            'fixed': '\n'.join(fixed_lines),
            'removed_count': len(unused_lines)
        }
    
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
        orig_lines = original.split('\n')
        fixed_lines = fixed.split('\n')
        
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
        
        return '\n'.join(diff)


class ExtractMagicNumbersFixer(BaseFixer):
    """Extracts magic numbers into named constants."""
    
    def __init__(self):
        super().__init__(name="extract_magic_numbers", risk_score=0.2)
    
    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview magic number extraction."""
        # Get the magic number from the issue metadata
        if 'value' not in issue.metadata:
            return FixResult(
                success=False,
                reason="No magic number value in issue metadata",
                risk_score=self.risk_score
            )
        
        magic_number = issue.metadata['value']
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
            risk_score=self.risk_score
        )
    
    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply magic number extraction."""
        return self.preview(issue, code)
    
    def _generate_constant_name(self, value, issue: CodeIssue) -> str:
        """Generate a meaningful constant name."""
        # Try to infer from context
        if 'context' in issue.metadata:
            context = issue.metadata['context']
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
    
    def __init__(self):
        super().__init__(name="add_docstrings", risk_score=0.1)
    
    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview docstring addition."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return FixResult(
                success=False,
                reason="Syntax error in code",
                risk_score=self.risk_score
            )
        
        # Find function/class needing docstring
        target_line = issue.line_number
        fixed_code = self._add_docstring(code, target_line)
        
        if fixed_code == code:
            return FixResult(
                success=False,
                reason="Could not add docstring",
                risk_score=self.risk_score
            )
        
        return FixResult(
            success=True,
            reason="Added docstring",
            diff=self._create_diff(code, fixed_code),
            original=code,
            fixed=fixed_code,
            risk_score=self.risk_score
        )
    
    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply docstring addition."""
        return self.preview(issue, code)
    
    def _add_docstring(self, code: str, line_number: int) -> str:
        """Add a docstring at the specified line."""
        lines = code.split('\n')
        
        if line_number > len(lines):
            return code
        
        # Get the function/class line
        func_line = lines[line_number - 1]
        indent = len(func_line) - len(func_line.lstrip())
        
        # Generate simple docstring
        docstring = ' ' * (indent + 4) + '"""TODO: Add description."""'
        
        # Insert after the function definition
        lines.insert(line_number, docstring)
        
        return '\n'.join(lines)
    
    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class RemoveDeadCodeFixer(BaseFixer):
    """Removes dead/unreachable code."""
    
    def __init__(self):
        super().__init__(name="remove_dead_code", risk_score=0.1)
    
    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview dead code removal."""
        # Simple implementation: remove the line indicated by the issue
        lines = code.split('\n')
        
        if issue.line_number > len(lines):
            return FixResult(
                success=False,
                reason="Invalid line number",
                risk_score=self.risk_score
            )
        
        # Remove the dead code line
        removed_line = lines[issue.line_number - 1]
        lines.pop(issue.line_number - 1)
        fixed = '\n'.join(lines)
        
        return FixResult(
            success=True,
            reason=f"Removed dead code: {removed_line.strip()}",
            diff=self._create_diff(code, fixed),
            original=code,
            fixed=fixed,
            risk_score=self.risk_score
        )
    
    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply dead code removal."""
        return self.preview(issue, code)
    
    def _create_diff(self, original: str, fixed: str) -> str:
        """Create a simple diff."""
        return f"--- Original\n{original}\n\n+++ Fixed\n{fixed}"


class FixTypeHintsFixer(BaseFixer):
    """Adds or fixes type hints."""
    
    def __init__(self):
        super().__init__(name="fix_type_hints", risk_score=0.4)
    
    def preview(self, issue: CodeIssue, code: str) -> FixResult:
        """Preview type hint fix."""
        # This is a more complex fixer that would require type inference
        # For now, return a placeholder
        return FixResult(
            success=False,
            reason="Type hint fixing not yet implemented",
            risk_score=self.risk_score
        )
    
    def apply(self, issue: CodeIssue, code: str) -> FixResult:
        """Apply type hint fix."""
        return self.preview(issue, code)

