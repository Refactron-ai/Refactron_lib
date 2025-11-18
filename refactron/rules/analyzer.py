"""Custom rule analyzer."""

from pathlib import Path
from typing import List

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.config import RefactronConfig
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel
from refactron.rules.loader import RuleLoader, RuleValidationError
from refactron.rules.matcher import PatternMatcher
from refactron.rules.models import CustomRule, RuleSeverity


class CustomRuleAnalyzer(BaseAnalyzer):
    """Analyzer that applies custom user-defined rules."""

    def __init__(self, config: RefactronConfig, rules_file: Path = None):
        """
        Initialize the custom rule analyzer.

        Args:
            config: Refactron configuration
            rules_file: Optional path to custom rules file. If not provided,
                       will look for .refactron-rules.yaml in current directory
        """
        super().__init__(config)
        self.loader = RuleLoader()
        self.matcher = PatternMatcher()
        self.custom_rules: List[CustomRule] = []

        # Try to load rules from file
        if rules_file is None:
            rules_file = Path(".refactron-rules.yaml")

        if rules_file.exists():
            try:
                ruleset = self.loader.load_from_file(rules_file)
                self.custom_rules = ruleset.rules
            except RuleValidationError as e:
                # Log error but don't fail - just skip custom rules
                print(f"Warning: Failed to load custom rules: {e}")

    def load_rules(self, rules_file: Path) -> None:
        """
        Load rules from a file.

        Args:
            rules_file: Path to the rules file

        Raises:
            RuleValidationError: If the rules file is invalid
        """
        ruleset = self.loader.load_from_file(rules_file)
        self.custom_rules = ruleset.rules

    def load_rules_from_string(self, yaml_content: str) -> None:
        """
        Load rules from a YAML string.

        Args:
            yaml_content: YAML content as a string

        Raises:
            RuleValidationError: If the YAML content is invalid
        """
        ruleset = self.loader.load_from_string(yaml_content)
        self.custom_rules = ruleset.rules

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze source code using custom rules.

        Args:
            file_path: Path to the file being analyzed
            source_code: Source code content

        Returns:
            List of detected code issues
        """
        issues = []

        # Get enabled rules
        enabled_rules = [rule for rule in self.custom_rules if rule.enabled]

        # Match each rule against the source code
        for rule in enabled_rules:
            matches = self.matcher.match(rule, file_path, source_code)

            for match in matches:
                # Convert match to CodeIssue
                issue = self._match_to_issue(match, file_path, source_code)
                issues.append(issue)

        return issues

    def _match_to_issue(
        self, match: "PatternMatch", file_path: Path, source_code: str
    ) -> CodeIssue:
        """
        Convert a pattern match to a CodeIssue.

        Args:
            match: Pattern match
            file_path: Path to the file
            source_code: Source code

        Returns:
            CodeIssue representing the match
        """
        rule = match.rule

        # Convert rule severity to issue level
        severity_map = {
            RuleSeverity.INFO: IssueLevel.INFO,
            RuleSeverity.WARNING: IssueLevel.WARNING,
            RuleSeverity.ERROR: IssueLevel.ERROR,
            RuleSeverity.CRITICAL: IssueLevel.CRITICAL,
        }
        level = severity_map.get(rule.severity, IssueLevel.WARNING)

        # Format message with context variables
        message = rule.message
        if match.context:
            for key, value in match.context.items():
                message = message.replace(f"{{{{{key}}}}}", str(value))

        # Get code snippet if not already provided
        code_snippet = match.code_snippet
        if not code_snippet and source_code:
            lines = source_code.split("\n")
            if 0 < match.line_number <= len(lines):
                code_snippet = lines[match.line_number - 1].strip()

        return CodeIssue(
            category=IssueCategory.STYLE,  # Custom rules are style-related by default
            level=level,
            message=message,
            file_path=file_path,
            line_number=match.line_number,
            column=match.column,
            end_line=match.end_line,
            code_snippet=code_snippet,
            suggestion=rule.suggestion,
            rule_id=rule.name,
            metadata={
                "custom_rule": True,
                "rule_name": rule.name,
                "rule_description": rule.description,
                **match.context,
            },
        )

    @property
    def name(self) -> str:
        """Return the name of this analyzer."""
        return "custom_rules"

    def get_loaded_rules(self) -> List[CustomRule]:
        """
        Get all loaded custom rules.

        Returns:
            List of loaded custom rules
        """
        return self.custom_rules

    def get_enabled_rules(self) -> List[CustomRule]:
        """
        Get only enabled custom rules.

        Returns:
            List of enabled custom rules
        """
        return [rule for rule in self.custom_rules if rule.enabled]
