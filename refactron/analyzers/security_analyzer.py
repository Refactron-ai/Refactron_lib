"""Analyzer for security vulnerabilities and unsafe patterns."""

import ast
from pathlib import Path
from typing import List

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel


class SecurityAnalyzer(BaseAnalyzer):
    """Detects common security vulnerabilities and unsafe code patterns."""

    # Dangerous functions that should be avoided
    DANGEROUS_FUNCTIONS = {
        "eval": "Code injection vulnerability - never use eval() with user input",
        "exec": "Code injection vulnerability - never use exec() with user input",
        "compile": "Potential code injection - use with extreme caution",
        "__import__": "Dynamic imports can be dangerous - use importlib instead",
        "input": "In Python 2, input() evaluates code - use raw_input() or upgrade to Python 3",
    }

    # Dangerous modules
    DANGEROUS_MODULES = {
        "pickle": "Unsafe deserialization - pickle can execute arbitrary code",
        "marshal": "Unsafe deserialization - use json instead",
        "shelve": "Uses pickle internally - vulnerable to code execution",
    }

    # Unsafe cryptographic modules
    WEAK_CRYPTO = {
        "md5": "MD5 is cryptographically broken - use SHA256 or better",
        "sha1": "SHA1 is deprecated - use SHA256 or better",
    }

    @property
    def name(self) -> str:
        return "security"

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze code for security vulnerabilities.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of security-related issues
        """
        issues = []

        try:
            tree = ast.parse(source_code)

            # Check for various security issues
            issues.extend(self._check_dangerous_functions(tree, file_path))
            issues.extend(self._check_dangerous_imports(tree, file_path))
            issues.extend(self._check_hardcoded_secrets(tree, file_path))
            issues.extend(self._check_sql_injection(tree, file_path))
            issues.extend(self._check_command_injection(tree, file_path))
            issues.extend(self._check_weak_crypto(tree, file_path))
            issues.extend(self._check_unsafe_yaml(tree, file_path))
            issues.extend(self._check_assert_statements(tree, file_path))

        except SyntaxError:
            pass

        return issues

    def _check_dangerous_functions(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for dangerous built-in functions."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                if func_name in self.DANGEROUS_FUNCTIONS:
                    issue = CodeIssue(
                        category=IssueCategory.SECURITY,
                        level=IssueLevel.CRITICAL,
                        message=f"Dangerous function '{func_name}()' used",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion=self.DANGEROUS_FUNCTIONS[func_name],
                        rule_id="SEC001",
                        metadata={"function": func_name},
                    )
                    issues.append(issue)

        return issues

    def _check_dangerous_imports(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for dangerous module imports."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = []

                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules = [node.module]

                for module in modules:
                    if module in self.DANGEROUS_MODULES:
                        issue = CodeIssue(
                            category=IssueCategory.SECURITY,
                            level=IssueLevel.WARNING,
                            message=f"Dangerous module '{module}' imported",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion=self.DANGEROUS_MODULES[module],
                            rule_id="SEC002",
                            metadata={"module": module},
                        )
                        issues.append(issue)

        return issues

    def _check_hardcoded_secrets(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for hardcoded passwords, API keys, tokens."""
        issues = []

        secret_patterns = [
            "password",
            "passwd",
            "pwd",
            "secret",
            "api_key",
            "apikey",
            "token",
            "auth",
            "credential",
            "private_key",
        ]

        # Common metadata variables that should be ignored (not actual secrets)
        metadata_whitelist = {
            "__author__",
            "__maintainer__",
            "__email__",
            "__version__",
            "__license__",
            "__copyright__",
            "__credits__",
            "__status__",
            "__date__",
            "__all__",
            "__name__",
            "__file__",
            "__doc__",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()

                        # Skip common package metadata variables
                        if target.id in metadata_whitelist:
                            continue

                        # Check if variable name suggests it contains a secret
                        if any(pattern in var_name for pattern in secret_patterns):
                            # Check if it's assigned a string literal
                            if isinstance(node.value, ast.Constant) and isinstance(
                                node.value.value, str
                            ):
                                value = node.value.value
                                # Ignore empty strings and obvious placeholders
                                if value and value not in ["", "TODO", "CHANGEME", "your-key-here"]:
                                    issue = CodeIssue(
                                        category=IssueCategory.SECURITY,
                                        level=IssueLevel.CRITICAL,
                                        message=(
                                            f"Potential hardcoded secret in variable '{target.id}'"
                                        ),
                                        file_path=file_path,
                                        line_number=node.lineno,
                                        suggestion=(
                                            "Store secrets in environment variables or a secure "
                                            "vault, never hardcode them in source code"
                                        ),
                                        rule_id="SEC003",
                                        metadata={"variable": target.id},
                                    )
                                    issues.append(issue)

        return issues

    def _check_sql_injection(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for potential SQL injection vulnerabilities."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                # Check for execute() calls with string formatting
                if func_name in ["execute", "executemany", "raw"]:
                    if node.args:
                        arg = node.args[0]

                        # Check for f-strings, % formatting, or .format()
                        if isinstance(arg, ast.JoinedStr):  # f-string
                            issue = CodeIssue(
                                category=IssueCategory.SECURITY,
                                level=IssueLevel.CRITICAL,
                                message="Potential SQL injection via f-string in execute()",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion=(
                                    "Use parameterized queries instead: cursor.execute(sql, "
                                    "(param1, param2))"
                                ),
                                rule_id="SEC004",
                            )
                            issues.append(issue)

                        elif isinstance(arg, ast.BinOp) and isinstance(
                            arg.op, ast.Mod
                        ):  # % formatting
                            issue = CodeIssue(
                                category=IssueCategory.SECURITY,
                                level=IssueLevel.CRITICAL,
                                message="Potential SQL injection via % formatting in execute()",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion=(
                                    "Use parameterized queries instead: cursor.execute(sql, "
                                    "(param1, param2))"
                                ),
                                rule_id="SEC004",
                            )
                            issues.append(issue)

        return issues

    def _check_command_injection(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for command injection vulnerabilities."""
        issues = []

        dangerous_calls = ["os.system", "subprocess.call", "subprocess.Popen", "os.popen"]

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_full_function_name(node.func)

                if any(dangerous in func_name for dangerous in dangerous_calls):
                    # Check if shell=True is used
                    for keyword in node.keywords:
                        if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                            if keyword.value.value is True:
                                issue = CodeIssue(
                                    category=IssueCategory.SECURITY,
                                    level=IssueLevel.CRITICAL,
                                    message=(
                                        f"Command injection risk: {func_name}() with shell=True"
                                    ),
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    suggestion=(
                                        "Avoid shell=True. Use subprocess with list of arguments "
                                        "instead"
                                    ),
                                    rule_id="SEC005",
                                )
                                issues.append(issue)

        return issues

    def _check_weak_crypto(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for weak cryptographic algorithms."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module == "hashlib":
                    for alias in node.names:
                        if alias.name in self.WEAK_CRYPTO:
                            issue = CodeIssue(
                                category=IssueCategory.SECURITY,
                                level=IssueLevel.WARNING,
                                message=f"Weak cryptographic algorithm: {alias.name}",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion=self.WEAK_CRYPTO[alias.name],
                                rule_id="SEC006",
                                metadata={"algorithm": alias.name},
                            )
                            issues.append(issue)

        return issues

    def _check_unsafe_yaml(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for unsafe YAML loading."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_full_function_name(node.func)

                if "yaml.load" in func_name and "safe_load" not in func_name:
                    issue = CodeIssue(
                        category=IssueCategory.SECURITY,
                        level=IssueLevel.ERROR,
                        message="Unsafe YAML loading with yaml.load()",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion=(
                            "Use yaml.safe_load() instead to prevent arbitrary code execution"
                        ),
                        rule_id="SEC007",
                    )
                    issues.append(issue)

        return issues

    def _check_assert_statements(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for assert statements used for security checks."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                # Asserts can be disabled with -O flag, making them unreliable for security
                issue = CodeIssue(
                    category=IssueCategory.SECURITY,
                    level=IssueLevel.INFO,
                    message="Assert statement used - can be disabled with -O flag",
                    file_path=file_path,
                    line_number=node.lineno,
                    suggestion="Don't use assert for security checks or input validation. "
                    "Use explicit if statements and raise exceptions instead",
                    rule_id="SEC008",
                )
                issues.append(issue)

        return issues

    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from a call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ""

    def _get_full_function_name(self, node: ast.AST) -> str:
        """Get full qualified function name (e.g., 'os.system')."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_full_function_name(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
            return node.attr
        return ""
