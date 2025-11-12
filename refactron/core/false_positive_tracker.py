"""False positive tracking system for security rules."""

import json
from pathlib import Path
from typing import Dict, List, Set


class FalsePositiveTracker:
    """Tracks and learns from false positive patterns."""

    def __init__(self, storage_path: Path = None):
        """
        Initialize the false positive tracker.

        Args:
            storage_path: Path to store false positive data
        """
        self.storage_path = storage_path or Path.home() / ".refactron" / "false_positives.json"
        self.false_positives: Dict[str, Set[str]] = {}
        self.load()

    def load(self) -> None:
        """Load false positive data from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.false_positives = {
                        rule_id: set(patterns) for rule_id, patterns in data.items()
                    }
            except (json.JSONDecodeError, IOError):
                self.false_positives = {}
        else:
            self.false_positives = {}

    def save(self) -> None:
        """Save false positive data to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {rule_id: list(patterns) for rule_id, patterns in self.false_positives.items()}
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def mark_false_positive(self, rule_id: str, pattern: str) -> None:
        """
        Mark a pattern as a false positive for a specific rule.

        Args:
            rule_id: The rule that produced the false positive
            pattern: The pattern that was incorrectly flagged
        """
        if rule_id not in self.false_positives:
            self.false_positives[rule_id] = set()
        self.false_positives[rule_id].add(pattern)
        self.save()

    def is_false_positive(self, rule_id: str, pattern: str) -> bool:
        """
        Check if a pattern is marked as a false positive.

        Args:
            rule_id: The rule to check
            pattern: The pattern to check

        Returns:
            True if the pattern is a known false positive
        """
        return rule_id in self.false_positives and pattern in self.false_positives[rule_id]

    def get_false_positive_patterns(self, rule_id: str) -> List[str]:
        """
        Get all false positive patterns for a rule.

        Args:
            rule_id: The rule ID

        Returns:
            List of false positive patterns
        """
        return list(self.false_positives.get(rule_id, set()))

    def clear_rule(self, rule_id: str) -> None:
        """
        Clear all false positives for a specific rule.

        Args:
            rule_id: The rule to clear
        """
        if rule_id in self.false_positives:
            del self.false_positives[rule_id]
            self.save()

    def clear_all(self) -> None:
        """Clear all false positive data."""
        self.false_positives = {}
        self.save()
