"""Integration test to demonstrate new analyzer features."""

import tempfile
from pathlib import Path

from refactron.core.config import RefactronConfig
from refactron.core.refactron import Refactron


def test_integrated_analyzer_coverage():
    """Test that all enhanced analyzers work together."""

    # Create a test file with various issues
    code = '''
import os
import sys
import random
import sqlite3
import requests

def problematic_function(a, b, c, d, e, f, g):
    """This function has many issues."""

    # Security: Insecure random
    token = random.randint(1000, 9999)

    # Security: SQL injection via string concatenation
    user_id = "123"
    query = "SELECT * FROM users WHERE id = " + user_id
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    cursor.execute(query)

    # Security: SSRF vulnerability
    url = f"http://api.example.com/{user_id}"
    response = requests.get(url, verify=False)

    # Complexity: Nested loops
    for i in range(10):
        for j in range(10):
            for k in range(10):
                for l in range(10):
                    print(i, j, k, l)

    # Performance: N+1 query
    items = [1, 2, 3, 4, 5]
    for item in items:
        cursor.execute("SELECT * FROM data WHERE id = ?", (item,))

    # Performance: Inefficient string concatenation
    result = ""
    for item in items:
        result += str(item)

    # Code smell: Repeated code
    x = items[0]
    y = x * 2
    z = y + 1
    first = z

    x = items[1]
    y = x * 2
    z = y + 1
    second = z

    return result
'''

    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        test_file = Path(f.name)

    try:
        # Initialize Refactron with all analyzers enabled
        config = RefactronConfig()
        refactron = Refactron(config)

        # Analyze the file
        result = refactron.analyze(test_file)

        # Verify we found issues from multiple analyzer types
        assert result.total_issues > 0, "Should find issues"

        # Check for security issues
        security_issues = [i for i in result.all_issues if i.category.value == "security"]
        assert len(security_issues) > 0, "Should find security issues"

        # Check for complexity issues
        complexity_issues = [i for i in result.all_issues if i.category.value == "complexity"]
        assert len(complexity_issues) > 0, "Should find complexity issues"

        # Check for performance issues
        performance_issues = [i for i in result.all_issues if i.category.value == "performance"]
        assert len(performance_issues) > 0, "Should find performance issues"

        # Check for code smell issues
        code_smell_issues = [i for i in result.all_issues if i.category.value == "code_smell"]
        assert len(code_smell_issues) > 0, "Should find code smell issues"

        # Verify specific new features work
        rule_ids = [i.rule_id for i in result.all_issues if i.rule_id]

        print(f"\nDetected rule IDs: {set(rule_ids)}")

        # Check new security features (at least one should be detected)
        security_new_features = ["SEC009", "SEC010", "SEC011", "SEC013"]
        assert any(
            rid in security_new_features for rid in rule_ids
        ), "Should detect at least one new security feature"

        # Check new complexity features
        assert any(rid == "C003" for rid in rule_ids), "Should detect nested loop depth"

        # Check new performance features
        performance_new_features = ["P001", "P005"]
        assert any(
            rid in performance_new_features for rid in rule_ids
        ), "Should detect at least one performance issue"

        # Check new code smell features
        assert any(rid == "S007" for rid in rule_ids), "Should detect repeated code blocks"

        print(f"✓ Found {result.total_issues} issues across all analyzers")
        print(f"  - Security: {len(security_issues)}")
        print(f"  - Complexity: {len(complexity_issues)}")
        print(f"  - Performance: {len(performance_issues)}")
        print(f"  - Code Smells: {len(code_smell_issues)}")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_integrated_analyzer_coverage()
    print("\n✓ Integration test passed!")
