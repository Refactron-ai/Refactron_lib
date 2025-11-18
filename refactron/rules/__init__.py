"""Custom rule framework for Refactron."""

from refactron.rules.analyzer import CustomRuleAnalyzer
from refactron.rules.loader import RuleLoader, RuleValidationError
from refactron.rules.matcher import PatternMatch, PatternMatcher
from refactron.rules.models import (
    CustomRule,
    PatternConfig,
    PatternType,
    RuleSeverity,
    RuleSet,
)
from refactron.rules.templates import (
    create_ruleset_from_templates,
    generate_example_ruleset,
    get_all_templates,
    get_template,
    list_templates,
)

__all__ = [
    # Analyzer
    "CustomRuleAnalyzer",
    # Loader
    "RuleLoader",
    "RuleValidationError",
    # Matcher
    "PatternMatcher",
    "PatternMatch",
    # Models
    "CustomRule",
    "PatternConfig",
    "PatternType",
    "RuleSeverity",
    "RuleSet",
    # Templates
    "get_template",
    "list_templates",
    "get_all_templates",
    "create_ruleset_from_templates",
    "generate_example_ruleset",
]
