"""Analyzer for security vulnerabilities and unsafe patterns."""

import ast
import fnmatch
from pathlib import Path
from typing import List

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel


class SecurityAnalyzer(BaseAnalyzer):
    """Detects common security vulnerabilities and unsafe code patterns."""

    # Confidence score constants
    TEST_FILE_CONFIDENCE_MULTIPLIER = 0.6
    DEMO_FILE_CONFIDENCE_MULTIPLIER = 0.7
    INSECURE_RANDOM_BASE_CONFIDENCE = 0.7

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

    # SSRF-prone functions
    SSRF_FUNCTIONS = {
        "requests.get",
        "requests.post",
        "requests.put",
        "requests.delete",
        "requests.patch",
        "urllib.request.urlopen",
        "urllib2.urlopen",
        "httplib.HTTPConnection",
        "httplib2.Http",
    }

    @property
    def name(self) -> str:
        return "security"

    def _is_ignored_file(self, file_path: Path) -> bool:
        """Check if file should be ignored for security checks."""
        path_str = str(file_path)
        for pattern in self.config.security_ignore_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
        return False

    def _is_rule_whitelisted(self, rule_id: str, file_path: Path) -> bool:
        """Check if a rule is whitelisted for a specific file."""
        whitelist = self.config.security_rule_whitelist.get(rule_id, [])
        path_str = str(file_path)
        for pattern in whitelist:
            if fnmatch.fnmatch(path_str, pattern):
                return True
        return False

    def _get_context_confidence(self, file_path: Path, rule_id: str) -> float:
        """
        Calculate confidence score based on file context.

        Args:
            file_path: Path to the file being analyzed
            rule_id: The rule being checked

        Returns:
            Confidence multiplier (0.0-1.0)
        """
        path_str = str(file_path).lower()

        # Test files get lower confidence for certain rules
        test_indicators = ["test_", "_test.", "tests/", "/test/", "testing/"]
        is_test_file = any(indicator in path_str for indicator in test_indicators)

        # Rules that are less critical in test files
        test_tolerant_rules = ["SEC001", "SEC002", "SEC011"]

        if is_test_file and rule_id in test_tolerant_rules:
            return self.TEST_FILE_CONFIDENCE_MULTIPLIER

        # Example/demo files get lower confidence
        demo_indicators = ["example", "demo", "sample", "tutorial"]
        is_demo_file = any(indicator in path_str for indicator in demo_indicators)

        if is_demo_file and rule_id in test_tolerant_rules:
            return self.DEMO_FILE_CONFIDENCE_MULTIPLIER

        return 1.0  # Default full confidence

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze code for security vulnerabilities.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of security-related issues
        """
        # Check if file is in ignore list
        if self._is_ignored_file(file_path):
            return []

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
            issues.extend(self._check_sql_parameterization(tree, file_path))
            issues.extend(self._check_ssrf_vulnerabilities(tree, file_path))
            issues.extend(self._check_insecure_random(tree, file_path))
            issues.extend(self._check_weak_ssl_tls(tree, file_path))

        except SyntaxError:
            pass

        # Filter out whitelisted rules and low confidence issues
        filtered_issues = []
        for issue in issues:
            if issue.rule_id and self._is_rule_whitelisted(issue.rule_id, file_path):
                continue

            if issue.confidence < self.config.security_min_confidence:
                continue

            filtered_issues.append(issue)

        return filtered_issues

    def _check_dangerous_functions(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for dangerous built-in functions."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                if func_name in self.DANGEROUS_FUNCTIONS:
                    # Calculate context-aware confidence
                    confidence = self._get_context_confidence(file_path, "SEC001")

                    issue = CodeIssue(
                        category=IssueCategory.SECURITY,
                        level=IssueLevel.CRITICAL,
                        message=f"Dangerous function '{func_name}()' used",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion=self.DANGEROUS_FUNCTIONS[func_name],
                        rule_id="SEC001",
                        confidence=confidence,
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
                        # Calculate context-aware confidence
                        confidence = self._get_context_confidence(file_path, "SEC002")

                        issue = CodeIssue(
                            category=IssueCategory.SECURITY,
                            level=IssueLevel.WARNING,
                            message=f"Dangerous module '{module}' imported",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion=self.DANGEROUS_MODULES[module],
                            rule_id="SEC002",
                            confidence=confidence,
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
                                    # Lower confidence for test/example files
                                    confidence = 0.8
                                    path_str = str(file_path).lower()
                                    if any(
                                        ind in path_str
                                        for ind in ["test", "example", "demo", "sample"]
                                    ):
                                        confidence = 0.5

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
                                        confidence=confidence,
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
                                confidence=0.9,
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
                                confidence=0.9,
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
                                    confidence=0.95,
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
                                confidence=0.85,
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
                        confidence=0.95,
                    )
                    issues.append(issue)

        return issues

    def _check_assert_statements(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for assert statements used for security checks."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                # Asserts can be disabled with -O flag, making them unreliable for security
                # Lower confidence since asserts are common and context-dependent
                issue = CodeIssue(
                    category=IssueCategory.SECURITY,
                    level=IssueLevel.INFO,
                    message="Assert statement used - can be disabled with -O flag",
                    file_path=file_path,
                    line_number=node.lineno,
                    suggestion="Don't use assert for security checks or input validation. "
                    "Use explicit if statements and raise exceptions instead",
                    rule_id="SEC008",
                    confidence=0.6,
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

    def _check_sql_parameterization(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for proper SQL parameterization usage."""
        issues = []

        # First pass: collect all variable assignments with string operations
        string_concat_vars = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Check if the assignment uses string concatenation or .format()
                        if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Add):
                            # Check if at least one side is a string
                            if isinstance(node.value.left, ast.Constant) or isinstance(
                                node.value.right, ast.Constant
                            ):
                                string_concat_vars[target.id] = node.lineno
                        elif isinstance(node.value, ast.Call) and isinstance(
                            node.value.func, ast.Attribute
                        ):
                            if node.value.func.attr == "format":
                                string_concat_vars[target.id] = node.lineno

        # Second pass: check execute() calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                # Check for execute() calls
                if func_name in ["execute", "executemany"]:
                    # Check if parameterized queries are being used properly
                    if len(node.args) >= 1:
                        arg = node.args[0]

                        # Check for string concatenation in SQL queries
                        if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                            issue = CodeIssue(
                                category=IssueCategory.SECURITY,
                                level=IssueLevel.CRITICAL,
                                message=(
                                    "SQL query uses string concatenation - "
                                    "use parameterized queries"
                                ),
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion=(
                                    "Use parameterized queries: cursor.execute("
                                    "'SELECT * FROM table WHERE id = ?', (value,))"
                                ),
                                rule_id="SEC009",
                                confidence=0.9,
                            )
                            issues.append(issue)

                        # Check for .format() method calls
                        elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
                            if arg.func.attr == "format":
                                issue = CodeIssue(
                                    category=IssueCategory.SECURITY,
                                    level=IssueLevel.CRITICAL,
                                    message=(
                                        "SQL query uses .format() - " "use parameterized queries"
                                    ),
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    suggestion=(
                                        "Use parameterized queries with placeholders "
                                        "instead of .format()"
                                    ),
                                    rule_id="SEC009",
                                    confidence=0.9,
                                )
                                issues.append(issue)

                        # Check if the variable was created with string concatenation/format
                        elif isinstance(arg, ast.Name) and arg.id in string_concat_vars:
                            issue = CodeIssue(
                                category=IssueCategory.SECURITY,
                                level=IssueLevel.CRITICAL,
                                message=(
                                    f"SQL query variable '{arg.id}' uses unsafe string "
                                    "operations - use parameterized queries"
                                ),
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion=(
                                    "Use parameterized queries: cursor.execute("
                                    "'SELECT * FROM table WHERE id = ?', (value,))"
                                ),
                                rule_id="SEC009",
                                confidence=0.85,
                            )
                            issues.append(issue)

        return issues

    def _check_ssrf_vulnerabilities(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for Server-Side Request Forgery (SSRF) vulnerabilities."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_full_function_name(node.func)

                # Check for HTTP request functions with user-controlled URLs
                for ssrf_func in self.SSRF_FUNCTIONS:
                    if ssrf_func in func_name:
                        # Check if URL parameter is potentially user-controlled
                        if node.args:
                            url_arg = node.args[0]

                            # Check for f-strings, format, or concatenation in URLs
                            is_dynamic = (
                                isinstance(url_arg, ast.JoinedStr)
                                or (
                                    isinstance(url_arg, ast.Call)
                                    and isinstance(url_arg.func, ast.Attribute)
                                    and url_arg.func.attr == "format"
                                )
                                or (
                                    isinstance(url_arg, ast.BinOp)
                                    and isinstance(url_arg.op, ast.Add)
                                )
                            )

                            if is_dynamic:
                                issue = CodeIssue(
                                    category=IssueCategory.SECURITY,
                                    level=IssueLevel.ERROR,
                                    message=(
                                        f"Potential SSRF vulnerability in {ssrf_func}() "
                                        "with dynamic URL"
                                    ),
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    suggestion=(
                                        "Validate and sanitize URLs. Use allowlists for domains. "
                                        "Avoid user-controlled URLs in HTTP requests."
                                    ),
                                    rule_id="SEC010",
                                    confidence=0.75,
                                    metadata={"function": ssrf_func},
                                )
                                issues.append(issue)

        return issues

    def _check_insecure_random(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for insecure random number generation."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # Check for random module imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "random":
                            # Lower confidence as random is often fine for non-security use
                            confidence = self._get_context_confidence(file_path, "SEC011")
                            issue = CodeIssue(
                                category=IssueCategory.SECURITY,
                                level=IssueLevel.WARNING,
                                message=("Using 'random' module - not cryptographically secure"),
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion=(
                                    "For security-sensitive operations, "
                                    "use 'secrets' module instead"
                                ),
                                rule_id="SEC011",
                                confidence=confidence * self.INSECURE_RANDOM_BASE_CONFIDENCE,
                            )
                            issues.append(issue)

        return issues

    def _check_weak_ssl_tls(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for weak SSL/TLS configurations."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for SSL context creation with weak settings
                if isinstance(node.func, ast.Attribute) and node.func.attr == "SSLContext":
                    for keyword in node.keywords:
                        if keyword.arg == "verify_mode" and isinstance(
                            keyword.value, ast.Attribute
                        ):
                            if "CERT_NONE" in self._get_full_function_name(keyword.value):
                                issue = CodeIssue(
                                    category=IssueCategory.SECURITY,
                                    level=IssueLevel.CRITICAL,
                                    message="SSL certificate verification disabled (CERT_NONE)",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    suggestion=(
                                        "Always verify SSL certificates. Use CERT_REQUIRED instead."
                                    ),
                                    rule_id="SEC012",
                                    confidence=0.95,
                                )
                                issues.append(issue)

                # Check for requests with verify=False
                func_name = self._get_full_function_name(node.func)
                if any(
                    req_func in func_name
                    for req_func in ["requests.get", "requests.post", "requests.request"]
                ):
                    for keyword in node.keywords:
                        if keyword.arg == "verify" and isinstance(keyword.value, ast.Constant):
                            if keyword.value.value is False:
                                issue = CodeIssue(
                                    category=IssueCategory.SECURITY,
                                    level=IssueLevel.CRITICAL,
                                    message="SSL certificate verification disabled (verify=False)",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    suggestion=(
                                        "Enable SSL verification. Remove verify=False parameter."
                                    ),
                                    rule_id="SEC013",
                                    confidence=0.95,
                                )
                                issues.append(issue)

        return issues
