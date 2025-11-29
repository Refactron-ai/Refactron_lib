"""Pattern matching engine for custom rules."""

import ast
import re
from pathlib import Path
from typing import List, Optional

from refactron.rules.models import CustomRule, PatternType


class PatternMatch:
    """Represents a matched pattern in code."""

    def __init__(
        self,
        rule: CustomRule,
        line_number: int,
        column: int = 0,
        end_line: Optional[int] = None,
        code_snippet: Optional[str] = None,
        context: Optional[dict] = None,
    ):
        """
        Initialize a pattern match.

        Args:
            rule: The rule that was matched
            line_number: Line number where the match occurred
            column: Column number where the match occurred
            end_line: End line number for multi-line matches
            code_snippet: Code snippet that matched
            context: Additional context about the match
        """
        self.rule = rule
        self.line_number = line_number
        self.column = column
        self.end_line = end_line
        self.code_snippet = code_snippet
        self.context = context or {}


class PatternMatcher:
    """Matches code patterns against custom rules."""

    def __init__(self):
        """Initialize the pattern matcher."""
        pass

    def match(self, rule: CustomRule, file_path: Path, source_code: str) -> List[PatternMatch]:
        """
        Match a rule against source code.

        Args:
            rule: The rule to match
            file_path: Path to the file being analyzed
            source_code: Source code to analyze

        Returns:
            List of pattern matches
        """
        # Check if file should be excluded/included
        if not self._should_analyze_file(rule, file_path):
            return []

        pattern_type = rule.pattern.type

        if pattern_type == PatternType.FUNCTION_CALL:
            return self._match_function_call(rule, source_code)
        elif pattern_type == PatternType.CLASS_DEF:
            return self._match_class_def(rule, source_code)
        elif pattern_type == PatternType.FUNCTION_DEF:
            return self._match_function_def(rule, source_code)
        elif pattern_type == PatternType.IMPORT:
            return self._match_import(rule, source_code)
        elif pattern_type == PatternType.ATTRIBUTE:
            return self._match_attribute(rule, source_code)
        elif pattern_type == PatternType.REGEX:
            return self._match_regex(rule, source_code)
        else:
            return []

    def _should_analyze_file(self, rule: CustomRule, file_path: Path) -> bool:
        """
        Check if a file should be analyzed based on include/exclude patterns.

        Args:
            rule: The rule to check
            file_path: Path to the file

        Returns:
            True if the file should be analyzed, False otherwise
        """
        # Check exclude patterns first
        for pattern in rule.exclude:
            if file_path.match(pattern):
                return False

        # If include patterns are specified, file must match at least one
        if rule.include:
            for pattern in rule.include:
                if file_path.match(pattern):
                    return True
            return False

        return True

    def _match_function_call(self, rule: CustomRule, source_code: str) -> List[PatternMatch]:
        """Match function call patterns."""
        matches = []
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return matches

        class FunctionCallVisitor(ast.NodeVisitor):
            def __init__(self, matcher: "PatternMatcher", rule: CustomRule):
                self.matcher = matcher
                self.rule = rule
                self.matches: List[PatternMatch] = []

            def visit_Call(self, node: ast.Call) -> None:
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name and func_name == self.rule.pattern.name:
                    # Check additional constraints
                    if self.matcher._check_constraints(node, self.rule.pattern.constraints):
                        match = PatternMatch(
                            rule=self.rule,
                            line_number=node.lineno,
                            column=node.col_offset,
                            context={"function_name": func_name},
                        )
                        self.matches.append(match)

                self.generic_visit(node)

        visitor = FunctionCallVisitor(self, rule)
        visitor.visit(tree)
        return visitor.matches

    def _match_class_def(self, rule: CustomRule, source_code: str) -> List[PatternMatch]:
        """Match class definition patterns."""
        matches = []
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return matches

        class ClassDefVisitor(ast.NodeVisitor):
            def __init__(self, matcher: "PatternMatcher", rule: CustomRule):
                self.matcher = matcher
                self.rule = rule
                self.matches: List[PatternMatch] = []

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                if self.rule.pattern.name is None or node.name == self.rule.pattern.name:
                    if self.matcher._check_constraints(node, self.rule.pattern.constraints):
                        match = PatternMatch(
                            rule=self.rule,
                            line_number=node.lineno,
                            column=node.col_offset,
                            context={"class_name": node.name},
                        )
                        self.matches.append(match)
                self.generic_visit(node)

        visitor = ClassDefVisitor(self, rule)
        visitor.visit(tree)
        return visitor.matches

    def _match_function_def(self, rule: CustomRule, source_code: str) -> List[PatternMatch]:
        """Match function definition patterns."""
        matches = []
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return matches

        class FunctionDefVisitor(ast.NodeVisitor):
            def __init__(self, matcher: "PatternMatcher", rule: CustomRule):
                self.matcher = matcher
                self.rule = rule
                self.matches: List[PatternMatch] = []
                self.source_lines = source_code.split("\n")

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                if self.rule.pattern.name is None or node.name == self.rule.pattern.name:
                    if self.matcher._check_constraints(node, self.rule.pattern.constraints):
                        # Calculate function length for constraints
                        end_line = node.end_lineno or node.lineno
                        func_length = end_line - node.lineno + 1

                        match = PatternMatch(
                            rule=self.rule,
                            line_number=node.lineno,
                            column=node.col_offset,
                            end_line=end_line,
                            context={"function_name": node.name, "lines": func_length},
                        )
                        self.matches.append(match)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                # Treat async functions the same as regular functions
                self.visit_FunctionDef(node)  # type: ignore

        visitor = FunctionDefVisitor(self, rule)
        visitor.visit(tree)
        return visitor.matches

    def _match_import(self, rule: CustomRule, source_code: str) -> List[PatternMatch]:
        """Match import patterns."""
        matches = []
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return matches

        class ImportVisitor(ast.NodeVisitor):
            def __init__(self, matcher: "PatternMatcher", rule: CustomRule):
                self.matcher = matcher
                self.rule = rule
                self.matches: List[PatternMatch] = []

            def visit_Import(self, node: ast.Import) -> None:
                for alias in node.names:
                    if self.rule.pattern.name is None or alias.name == self.rule.pattern.name:
                        match = PatternMatch(
                            rule=self.rule,
                            line_number=node.lineno,
                            column=node.col_offset,
                            context={"module": alias.name},
                        )
                        self.matches.append(match)
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                module = node.module or ""
                for alias in node.names:
                    import_name = f"{module}.{alias.name}" if module else alias.name
                    if self.rule.pattern.name is None or import_name == self.rule.pattern.name:
                        match = PatternMatch(
                            rule=self.rule,
                            line_number=node.lineno,
                            column=node.col_offset,
                            context={"module": import_name},
                        )
                        self.matches.append(match)
                self.generic_visit(node)

        visitor = ImportVisitor(self, rule)
        visitor.visit(tree)
        return visitor.matches

    def _match_attribute(self, rule: CustomRule, source_code: str) -> List[PatternMatch]:
        """Match attribute access patterns."""
        matches = []
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return matches

        class AttributeVisitor(ast.NodeVisitor):
            def __init__(self, matcher: "PatternMatcher", rule: CustomRule):
                self.matcher = matcher
                self.rule = rule
                self.matches: List[PatternMatch] = []

            def visit_Attribute(self, node: ast.Attribute) -> None:
                if self.rule.pattern.name is None or node.attr == self.rule.pattern.name:
                    match = PatternMatch(
                        rule=self.rule,
                        line_number=node.lineno,
                        column=node.col_offset,
                        context={"attribute": node.attr},
                    )
                    self.matches.append(match)
                self.generic_visit(node)

        visitor = AttributeVisitor(self, rule)
        visitor.visit(tree)
        return visitor.matches

    def _match_regex(self, rule: CustomRule, source_code: str) -> List[PatternMatch]:
        """Match regex patterns."""
        matches = []
        if not rule.pattern.regex:
            return matches

        try:
            pattern = re.compile(rule.pattern.regex, re.MULTILINE)
        except re.error:
            return matches

        # Precompute line start indices for efficient line number calculation
        line_start_indices = [0]
        for match in re.finditer(r"\n", source_code):
            line_start_indices.append(match.end())

        def get_line_number(pos: int) -> int:
            """Binary search for the line number given a character position."""
            left, right = 0, len(line_start_indices) - 1
            while left <= right:
                mid = (left + right) // 2
                if mid + 1 < len(line_start_indices):
                    if line_start_indices[mid] <= pos < line_start_indices[mid + 1]:
                        return mid + 1  # line numbers are 1-based
                else:
                    if pos >= line_start_indices[mid]:
                        return mid + 1
                if pos < line_start_indices[mid]:
                    right = mid - 1
                else:
                    left = mid + 1
            return len(line_start_indices)

        # Match against entire source code at once for better performance
        for match in pattern.finditer(source_code):
            start_pos = match.start()
            line_number = get_line_number(start_pos)
            column = start_pos - line_start_indices[line_number - 1]
            pattern_match = PatternMatch(
                rule=rule,
                line_number=line_number,
                column=column,
                code_snippet=match.group(),
            )
            matches.append(pattern_match)

        return matches

    def _check_constraints(self, node: ast.AST, constraints: dict) -> bool:
        """
        Check if a node meets the specified constraints.

        Args:
            node: AST node to check
            constraints: Dictionary of constraints

        Returns:
            True if all constraints are met, False otherwise
        """
        if not constraints:
            return True

        # Check line count constraints for functions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if "lines" in constraints:
                end_line = node.end_lineno or node.lineno
                func_length = end_line - node.lineno + 1
                constraint = constraints["lines"]

                if isinstance(constraint, str):
                    # Parse constraint like "> 50" or "< 10"
                    if constraint.startswith(">"):
                        threshold = int(constraint[1:].strip())
                        if func_length <= threshold:
                            return False
                    elif constraint.startswith("<"):
                        threshold = int(constraint[1:].strip())
                        if func_length >= threshold:
                            return False
                elif isinstance(constraint, int):
                    if func_length != constraint:
                        return False

            # Check parameter count
            if "params" in constraints:
                param_count = len(node.args.args)
                constraint = constraints["params"]

                if isinstance(constraint, str):
                    if constraint.startswith(">"):
                        threshold = int(constraint[1:].strip())
                        if param_count <= threshold:
                            return False
                    elif constraint.startswith("<"):
                        threshold = int(constraint[1:].strip())
                        if param_count >= threshold:
                            return False
                elif isinstance(constraint, int):
                    if param_count != constraint:
                        return False

        return True
