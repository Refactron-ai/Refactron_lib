#!/usr/bin/env python3
"""
Phase 2 Demo - Advanced Analysis

Shows off all Phase 2 analyzers in action!
"""

from refactron import Refactron
from refactron.core.config import RefactronConfig


def demo_security_analyzer():
    """Demo security vulnerability detection."""
    print("\n" + "=" * 80)
    print("🔒 SECURITY ANALYZER DEMO")
    print("=" * 80)

    code_with_vulnerabilities = """
import pickle

# Security issues:
api_key = "sk_live_abc123"  # Hardcoded secret
password = "mysecretpass"    # Hardcoded password

def dangerous_function(user_input):
    result = eval(user_input)  # Code injection!
    return result

def load_data(filename):
    with open(filename, 'rb') as f:
        data = pickle.load(f)  # Unsafe deserialization!
    return data

def get_user(username):
    # SQL injection vulnerability!
    query = f"SELECT * FROM users WHERE name = '{username}'"
    cursor.execute(query)
    return cursor.fetchall()
"""

    config = RefactronConfig(enabled_analyzers=["security"])
    refactron = Refactron(config)

    with open("/tmp/test_security.py", "w") as f:
        f.write(code_with_vulnerabilities)

    result = refactron.analyze("/tmp/test_security.py")

    print(f"\n🔍 Found {result.total_issues} security issues:\n")

    for issue in result.all_issues:
        icon = "🔴" if issue.level.value == "critical" else "⚠️"
        print(f"{icon} {issue.level.value.upper()}: {issue.message}")
        print(f"   Line {issue.line_number}")
        if issue.suggestion:
            print(f"   💡 {issue.suggestion}")
        print()


def demo_dependency_analyzer():
    """Demo dependency analysis."""
    print("\n" + "=" * 80)
    print("📦 DEPENDENCY ANALYZER DEMO")
    print("=" * 80)

    code_with_dependency_issues = """
import os
import sys
import json  # Unused!
from pathlib import *  # Wildcard import!
import imp  # Deprecated!

def main():
    def helper():
        import time  # Import inside function - circular dependency pattern!
        return time.time()

    print("Hello from", sys.argv[0])
    return helper()
"""

    config = RefactronConfig(enabled_analyzers=["dependency"])
    refactron = Refactron(config)

    with open("/tmp/test_dependency.py", "w") as f:
        f.write(code_with_dependency_issues)

    result = refactron.analyze("/tmp/test_dependency.py")

    print(f"\n🔍 Found {result.total_issues} dependency issues:\n")

    for issue in result.all_issues:
        icon = "⚠️" if issue.level.value == "warning" else "ℹ️"
        print(f"{icon} {issue.message}")
        print(f"   Line {issue.line_number}")
        if issue.suggestion:
            print(f"   💡 {issue.suggestion[:80]}...")
        print()


def demo_dead_code_analyzer():
    """Demo dead code detection."""
    print("\n" + "=" * 80)
    print("💀 DEAD CODE ANALYZER DEMO")
    print("=" * 80)

    code_with_dead_code = """
def used_function():
    return 42

def unused_function():  # Never called!
    return 100

def function_with_unreachable():
    return 42
    print("This will never execute!")  # Unreachable!
    x = 100

def empty_placeholder():  # Empty function!
    pass

def redundant_check(x):
    if True:  # Always true!
        return "always"

    if x == True:  # Redundant comparison!
        return "redundant"

result = used_function()
"""

    config = RefactronConfig(enabled_analyzers=["dead_code"])
    refactron = Refactron(config)

    with open("/tmp/test_dead_code.py", "w") as f:
        f.write(code_with_dead_code)

    result = refactron.analyze("/tmp/test_dead_code.py")

    print(f"\n🔍 Found {result.total_issues} dead code issues:\n")

    for issue in result.all_issues:
        icon = "⚠️" if issue.level.value == "warning" else "ℹ️"
        print(f"{icon} {issue.message}")
        print(f"   Line {issue.line_number}")
        if issue.suggestion:
            print(f"   💡 {issue.suggestion[:80]}...")
        print()


def demo_type_hint_analyzer():
    """Demo type hint analysis."""
    print("\n" + "=" * 80)
    print("🏷️  TYPE HINT ANALYZER DEMO")
    print("=" * 80)

    code_without_types = """
from typing import Any, List

def process_data(data, flag):  # Missing parameter types!
    return data if flag else None  # Missing return type!

def get_items():  # Missing return type!
    return []

def get_mapping() -> Dict:  # Incomplete generic!
    return {}

def unsafe_process(data: Any) -> Any:  # Uses Any - defeats type checking!
    return data

class DataProcessor:
    value = 42  # Missing attribute type!

    def method(self, x):  # Missing parameter and return types!
        return x * 2
"""

    config = RefactronConfig(enabled_analyzers=["type_hints"])
    refactron = Refactron(config)

    with open("/tmp/test_types.py", "w") as f:
        f.write(code_without_types)

    result = refactron.analyze("/tmp/test_types.py")

    print(f"\n🔍 Found {result.total_issues} type hint issues:\n")

    for issue in result.all_issues[:10]:  # Show first 10
        print(f"ℹ️ {issue.message}")
        print(f"   Line {issue.line_number}")
        if issue.suggestion:
            print(f"   💡 {issue.suggestion[:80]}...")
        print()

    if result.total_issues > 10:
        print(f"... and {result.total_issues - 10} more")


def demo_all_analyzers():
    """Demo all Phase 2 analyzers together."""
    print("\n" + "=" * 80)
    print("🎯 ALL ANALYZERS TOGETHER")
    print("=" * 80)

    code_with_multiple_issues = """
import os
import json  # Unused!

api_key = "secret123"  # Hardcoded secret!

def process_data(data):  # Missing type hints!
    if True:  # Always true!
        result = eval(data)  # Security issue!
        return result  # Missing return type!

def unused_helper():  # Never called!
    pass  # Empty function!
"""

    config = RefactronConfig(
        enabled_analyzers=["security", "dependency", "dead_code", "type_hints"]
    )
    refactron = Refactron(config)

    with open("/tmp/test_all.py", "w") as f:
        f.write(code_with_multiple_issues)

    result = refactron.analyze("/tmp/test_all.py")

    print(f"\n🔍 Found {result.total_issues} total issues:\n")

    # Group by category
    by_category = {}
    for issue in result.all_issues:
        category = issue.category.value
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(issue)

    for category, issues in by_category.items():
        icon = {"security": "🔒", "dependency": "📦", "dead_code": "💀", "type_hints": "🏷️"}
        print(f"{icon.get(category, '•')} {category.upper()}: {len(issues)} issues")
        for issue in issues[:2]:  # Show first 2 per category
            print(f"   • {issue.message}")
        if len(issues) > 2:
            print(f"   ... and {len(issues) - 2} more")
        print()


def main():
    """Run all Phase 2 demos."""
    print("\n" + "🎉" * 40)
    print("REFACTRON PHASE 2 - ADVANCED ANALYSIS DEMO")
    print("🎉" * 40)

    try:
        demo_security_analyzer()
        input("\n[Press Enter to continue...]")

        demo_dependency_analyzer()
        input("\n[Press Enter to continue...]")

        demo_dead_code_analyzer()
        input("\n[Press Enter to continue...]")

        demo_type_hint_analyzer()
        input("\n[Press Enter to continue...]")

        demo_all_analyzers()

        print("\n" + "=" * 80)
        print("✨ PHASE 2 DEMO COMPLETE!")
        print("=" * 80)
        print(
            """
Phase 2 Added:
✅ Security Analyzer - 8 vulnerability types
✅ Dependency Analyzer - 7 import issues
✅ Dead Code Analyzer - 5 dead code patterns
✅ Type Hint Analyzer - 5 type hint issues

Total: 25+ new issue types detected!

Try it yourself:
  refactron analyze your_code.py
"""
        )

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
