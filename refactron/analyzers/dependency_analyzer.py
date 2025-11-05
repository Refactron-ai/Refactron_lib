"""Analyzer for import dependencies and module relationships."""

import ast
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Set, Tuple

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel

if TYPE_CHECKING:
    from refactron.core.config import RefactronConfig


class DependencyAnalyzer(BaseAnalyzer):
    """Analyzes import statements and dependencies."""

    def __init__(self, config: "RefactronConfig") -> None:
        super().__init__(config)
        self.stdlib_modules = self._get_stdlib_modules()

    @property
    def name(self) -> str:
        return "dependency"

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze imports and dependencies.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of dependency-related issues
        """
        issues = []

        try:
            tree = ast.parse(source_code)

            # Check for various dependency issues
            issues.extend(self._check_unused_imports(tree, file_path, source_code))
            issues.extend(self._check_wildcard_imports(tree, file_path))
            issues.extend(self._check_circular_imports(tree, file_path))
            issues.extend(self._check_import_order(tree, file_path))
            issues.extend(self._check_relative_imports(tree, file_path))
            issues.extend(self._check_duplicate_imports(tree, file_path))
            issues.extend(self._check_deprecated_modules(tree, file_path))

        except SyntaxError:
            pass

        return issues

    def _check_unused_imports(
        self, tree: ast.AST, file_path: Path, source_code: str
    ) -> List[CodeIssue]:
        """Detect imported modules that are never used."""
        issues = []

        # Collect all imports
        imports: Dict[str, int] = {}  # name -> line_number

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = node.lineno

            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = node.lineno

        # Check if each import is used
        for import_name, line_num in imports.items():
            # Simple heuristic: check if the name appears elsewhere in the code
            used = False

            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == import_name:
                    # Check if this is not the import statement itself
                    if not (
                        isinstance(node.ctx, ast.Store) and getattr(node, "lineno", 0) == line_num
                    ):
                        used = True
                        break

                elif isinstance(node, ast.Attribute):
                    if self._get_root_name(node) == import_name:
                        used = True
                        break

            if not used and import_name != "__future__":
                issue = CodeIssue(
                    category=IssueCategory.MAINTAINABILITY,
                    level=IssueLevel.INFO,
                    message=f"Unused import: '{import_name}'",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion=f"Remove unused import '{import_name}' to keep code clean",
                    rule_id="DEP001",
                    metadata={"import": import_name},
                )
                issues.append(issue)

        return issues

    def _check_wildcard_imports(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for wildcard imports (from module import *)."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        module = node.module or "module"
                        issue = CodeIssue(
                            category=IssueCategory.MAINTAINABILITY,
                            level=IssueLevel.WARNING,
                            message=f"Wildcard import from '{module}'",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="Wildcard imports pollute namespace and hide dependencies. "
                            "Import specific names instead",
                            rule_id="DEP002",
                            metadata={"module": module},
                        )
                        issues.append(issue)

        return issues

    def _check_circular_imports(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Detect potential circular import issues."""
        issues = []

        # Check for imports inside functions (often done to avoid circular imports)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if isinstance(child, (ast.Import, ast.ImportFrom)):
                        module = getattr(child, "module", None) or (
                            child.names[0].name if hasattr(child, "names") else "unknown"
                        )

                        issue = CodeIssue(
                            category=IssueCategory.MAINTAINABILITY,
                            level=IssueLevel.WARNING,
                            message=(
                                f"Import inside function '{node.name}' may indicate circular "
                                f"dependency"
                            ),
                            file_path=file_path,
                            line_number=child.lineno,
                            suggestion=(
                                "Move imports to module level if possible. "
                                "If avoiding circular imports, consider restructuring modules"
                            ),
                            rule_id="DEP003",
                            metadata={"module": module, "function": node.name},
                        )
                        issues.append(issue)
                        break  # Only report once per function

        return issues

    def _check_import_order(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check if imports follow standard ordering (stdlib, third-party, local)."""
        issues = []

        imports: List[Tuple[int, str, str]] = []  # (line, type, module)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                module = node.names[0].name.split(".")[0]
                import_type = self._classify_import(module)
                imports.append((node.lineno, import_type, module))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0]
                    import_type = self._classify_import(module)
                    imports.append((node.lineno, import_type, module))

        # Check if imports are ordered correctly
        if len(imports) > 1:
            expected_order = ["stdlib", "third_party", "local"]
            prev_type_idx = -1

            for line, import_type, module in imports:
                type_idx = expected_order.index(import_type) if import_type in expected_order else 2

                if type_idx < prev_type_idx:
                    issue = CodeIssue(
                        category=IssueCategory.STYLE,
                        level=IssueLevel.INFO,
                        message=(
                            f"Import order: {import_type} import after "
                            f"{expected_order[prev_type_idx]}"
                        ),
                        file_path=file_path,
                        line_number=line,
                        suggestion=(
                            "Follow PEP 8 import order: stdlib, third-party, then local imports"
                        ),
                        rule_id="DEP004",
                        metadata={"module": module},
                    )
                    issues.append(issue)
                    break  # Only report once

                prev_type_idx = type_idx

        return issues

    def _check_relative_imports(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for relative imports."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level > 0:  # Relative import (from . import ...)
                    issue = CodeIssue(
                        category=IssueCategory.STYLE,
                        level=IssueLevel.INFO,
                        message=f"Relative import with level {node.level}",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Consider using absolute imports for better clarity. "
                        "Relative imports can be confusing in large projects",
                        rule_id="DEP005",
                        metadata={"level": node.level},
                    )
                    issues.append(issue)

        return issues

    def _check_duplicate_imports(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for duplicate imports."""
        issues = []

        seen_imports: Dict[str, int] = {}  # module -> first occurrence line

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    if module in seen_imports:
                        issue = CodeIssue(
                            category=IssueCategory.MAINTAINABILITY,
                            level=IssueLevel.WARNING,
                            message=f"Duplicate import: '{module}'",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion=(
                                f"Remove duplicate import. First imported at line "
                                f"{seen_imports[module]}"
                            ),
                            rule_id="DEP006",
                            metadata={"module": module, "first_line": seen_imports[module]},
                        )
                        issues.append(issue)
                    else:
                        seen_imports[module] = node.lineno

        return issues

    def _check_deprecated_modules(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for imports of deprecated modules."""
        issues = []

        deprecated = {
            "imp": "Use importlib instead",
            "optparse": "Use argparse instead",
            "xml.etree.cElementTree": (
                "Use xml.etree.ElementTree instead (C implementation is default in " "Python 3.3+)"
            ),
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in deprecated:
                        issue = CodeIssue(
                            category=IssueCategory.MODERNIZATION,
                            level=IssueLevel.WARNING,
                            message=f"Deprecated module imported: '{alias.name}'",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion=deprecated[alias.name],
                            rule_id="DEP007",
                            metadata={"module": alias.name},
                        )
                        issues.append(issue)

            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module in deprecated:
                    issue = CodeIssue(
                        category=IssueCategory.MODERNIZATION,
                        level=IssueLevel.WARNING,
                        message=f"Deprecated module imported: '{node.module}'",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion=deprecated[node.module],
                        rule_id="DEP007",
                        metadata={"module": node.module},
                    )
                    issues.append(issue)

        return issues

    def _classify_import(self, module: str) -> str:
        """Classify import as stdlib, third_party, or local."""
        if module in self.stdlib_modules:
            return "stdlib"
        elif module.startswith("."):
            return "local"
        else:
            # Heuristic: lowercase single word is likely third-party
            return "third_party" if "_" in module or module.islower() else "local"

    def _get_stdlib_modules(self) -> Set[str]:
        """Get set of Python standard library module names."""
        # Common Python 3 stdlib modules
        return {
            "abc",
            "aifc",
            "argparse",
            "array",
            "ast",
            "asynchat",
            "asyncio",
            "asyncore",
            "atexit",
            "audioop",
            "base64",
            "bdb",
            "binascii",
            "binhex",
            "bisect",
            "builtins",
            "bz2",
            "calendar",
            "cgi",
            "cgitb",
            "chunk",
            "cmath",
            "cmd",
            "code",
            "codecs",
            "codeop",
            "collections",
            "colorsys",
            "compileall",
            "concurrent",
            "configparser",
            "contextlib",
            "contextvars",
            "copy",
            "copyreg",
            "cProfile",
            "crypt",
            "csv",
            "ctypes",
            "curses",
            "dataclasses",
            "datetime",
            "dbm",
            "decimal",
            "difflib",
            "dis",
            "distutils",
            "doctest",
            "email",
            "encodings",
            "enum",
            "errno",
            "faulthandler",
            "fcntl",
            "filecmp",
            "fileinput",
            "fnmatch",
            "formatter",
            "fractions",
            "ftplib",
            "functools",
            "gc",
            "getopt",
            "getpass",
            "gettext",
            "glob",
            "graphlib",
            "grp",
            "gzip",
            "hashlib",
            "heapq",
            "hmac",
            "html",
            "http",
            "imaplib",
            "imghdr",
            "imp",
            "importlib",
            "inspect",
            "io",
            "ipaddress",
            "itertools",
            "json",
            "keyword",
            "lib2to3",
            "linecache",
            "locale",
            "logging",
            "lzma",
            "mailbox",
            "mailcap",
            "marshal",
            "math",
            "mimetypes",
            "mmap",
            "modulefinder",
            "multiprocessing",
            "netrc",
            "nis",
            "nntplib",
            "numbers",
            "operator",
            "optparse",
            "os",
            "ossaudiodev",
            "parser",
            "pathlib",
            "pdb",
            "pickle",
            "pickletools",
            "pipes",
            "pkgutil",
            "platform",
            "plistlib",
            "poplib",
            "posix",
            "posixpath",
            "pprint",
            "profile",
            "pstats",
            "pty",
            "pwd",
            "py_compile",
            "pyclbr",
            "pydoc",
            "queue",
            "quopri",
            "random",
            "re",
            "readline",
            "reprlib",
            "resource",
            "rlcompleter",
            "runpy",
            "sched",
            "secrets",
            "select",
            "selectors",
            "shelve",
            "shlex",
            "shutil",
            "signal",
            "site",
            "smtpd",
            "smtplib",
            "sndhdr",
            "socket",
            "socketserver",
            "spwd",
            "sqlite3",
            "ssl",
            "stat",
            "statistics",
            "string",
            "stringprep",
            "struct",
            "subprocess",
            "sunau",
            "symbol",
            "symtable",
            "sys",
            "sysconfig",
            "syslog",
            "tabnanny",
            "tarfile",
            "telnetlib",
            "tempfile",
            "termios",
            "test",
            "textwrap",
            "threading",
            "time",
            "timeit",
            "tkinter",
            "token",
            "tokenize",
            "tomllib",
            "trace",
            "traceback",
            "tracemalloc",
            "tty",
            "turtle",
            "turtledemo",
            "types",
            "typing",
            "unicodedata",
            "unittest",
            "urllib",
            "uu",
            "uuid",
            "venv",
            "warnings",
            "wave",
            "weakref",
            "webbrowser",
            "winreg",
            "winsound",
            "wsgiref",
            "xdrlib",
            "xml",
            "xmlrpc",
            "zipapp",
            "zipfile",
            "zipimport",
            "zlib",
            "zoneinfo",
        }

    def _get_root_name(self, node: ast.Attribute) -> str:
        """Get the root name from an attribute chain (e.g., 'os' from 'os.path.join')."""
        if isinstance(node.value, ast.Name):
            return node.value.id
        elif isinstance(node.value, ast.Attribute):
            return self._get_root_name(node.value)
        return ""
