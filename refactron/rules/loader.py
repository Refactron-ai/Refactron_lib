"""Rule loader and validator for custom rules."""

import re
from pathlib import Path
from typing import List

import yaml

from refactron.rules.models import CustomRule, RuleSet


class RuleValidationError(Exception):
    """Exception raised when rule validation fails."""

    pass


class RuleLoader:
    """Loads and validates custom rules from YAML files."""

    def __init__(self):
        """Initialize the rule loader."""
        self.loaded_rules: List[CustomRule] = []

    def load_from_file(self, file_path: Path) -> RuleSet:
        """
        Load rules from a YAML file.

        Args:
            file_path: Path to the YAML file containing rules

        Returns:
            RuleSet containing loaded rules

        Raises:
            RuleValidationError: If the file is invalid or rules fail validation
        """
        if not file_path.exists():
            raise RuleValidationError(f"Rule file not found: {file_path}")

        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RuleValidationError(f"Invalid YAML file: {e}")

        if not data:
            raise RuleValidationError("Empty rule file")

        try:
            ruleset = RuleSet.from_dict(data)
        except Exception as e:
            raise RuleValidationError(f"Failed to parse rules: {e}")

        # Validate each rule
        for rule in ruleset.rules:
            self._validate_rule(rule)

        self.loaded_rules = ruleset.rules
        return ruleset

    def load_from_string(self, yaml_content: str) -> RuleSet:
        """
        Load rules from a YAML string.

        Args:
            yaml_content: YAML content as a string

        Returns:
            RuleSet containing loaded rules

        Raises:
            RuleValidationError: If the content is invalid or rules fail validation
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise RuleValidationError(f"Invalid YAML content: {e}")

        if not data:
            raise RuleValidationError("Empty rule content")

        try:
            ruleset = RuleSet.from_dict(data)
        except Exception as e:
            raise RuleValidationError(f"Failed to parse rules: {e}")

        # Validate each rule
        for rule in ruleset.rules:
            self._validate_rule(rule)

        self.loaded_rules = ruleset.rules
        return ruleset

    def _validate_rule(self, rule: CustomRule) -> None:
        """
        Validate a custom rule.

        Args:
            rule: Rule to validate

        Raises:
            RuleValidationError: If the rule is invalid
        """
        # Validate name
        if not rule.name:
            raise RuleValidationError("Rule name is required")

        if not re.match(r"^[a-z0-9-_]+$", rule.name):
            raise RuleValidationError(
                f"Invalid rule name '{rule.name}'. "
                "Names must contain only lowercase letters, numbers, hyphens, and underscores"
            )

        # Validate description
        if not rule.description:
            raise RuleValidationError(f"Rule '{rule.name}' requires a description")

        # Validate message
        if not rule.message:
            raise RuleValidationError(f"Rule '{rule.name}' requires a message")

        # Validate pattern
        pattern = rule.pattern
        if pattern.type.value == "function_call" and not pattern.name:
            raise RuleValidationError(f"Rule '{rule.name}': function_call pattern requires a name")

        if pattern.type.value == "regex" and not pattern.regex:
            raise RuleValidationError(f"Rule '{rule.name}': regex pattern requires a regex field")

        # Validate regex pattern if provided
        if pattern.regex:
            try:
                re.compile(pattern.regex)
            except re.error as e:
                raise RuleValidationError(f"Rule '{rule.name}': invalid regex pattern: {e}")

        # Validate exclude/include patterns
        for pattern_str in rule.exclude + rule.include:
            if not pattern_str:
                raise RuleValidationError(f"Rule '{rule.name}': empty pattern in exclude/include")

    def get_rules(self) -> List[CustomRule]:
        """
        Get all loaded rules.

        Returns:
            List of loaded custom rules
        """
        return self.loaded_rules

    def get_enabled_rules(self) -> List[CustomRule]:
        """
        Get only enabled rules.

        Returns:
            List of enabled custom rules
        """
        return [rule for rule in self.loaded_rules if rule.enabled]
