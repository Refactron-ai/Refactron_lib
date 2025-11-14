#!/usr/bin/env python3
"""
Refactron Demo Script

This script demonstrates the basic functionality of Refactron.
Run this to see Refactron in action!
"""

from pathlib import Path

from refactron import Refactron
from refactron.core.config import RefactronConfig


def demo_analysis():
    """Demonstrate code analysis."""
    print("\n" + "=" * 80)
    print("REFACTRON DEMO - CODE ANALYSIS")
    print("=" * 80 + "\n")

    # Create Refactron instance
    refactron = Refactron()

    # Analyze the bad code example
    example_file = Path(__file__).parent / "bad_code_example.py"

    if not example_file.exists():
        print("❌ Example file not found!")
        return

    print(f"📂 Analyzing: {example_file}")
    print("-" * 80)

    # Run analysis
    result = refactron.analyze(example_file)

    # Display results
    print(result.report(detailed=True))

    # Show summary
    summary = result.summary()
    print("\n📊 Quick Summary:")
    print(f"   Files: {summary['total_files']}")
    print(f"   Issues: {summary['total_issues']}")
    print(f"   Critical: {summary['critical']}")
    print(f"   Errors: {summary['errors']}")
    print(f"   Warnings: {summary['warnings']}")


def demo_refactoring():
    """Demonstrate refactoring suggestions."""
    print("\n" + "=" * 80)
    print("REFACTRON DEMO - REFACTORING SUGGESTIONS")
    print("=" * 80 + "\n")

    # Create Refactron instance
    refactron = Refactron()

    # Analyze the bad code example
    example_file = Path(__file__).parent / "bad_code_example.py"

    if not example_file.exists():
        print("❌ Example file not found!")
        return

    print(f"📂 Refactoring: {example_file}")
    print("-" * 80)

    # Run refactoring analysis
    result = refactron.refactor(example_file, preview=True)

    if result.operations:
        print(result.show_diff())
        print(f"\n✅ Found {result.total_operations} refactoring opportunities!")
    else:
        print("\n✅ No refactoring suggestions (code looks good!)")


def demo_custom_config():
    """Demonstrate custom configuration."""
    print("\n" + "=" * 80)
    print("REFACTRON DEMO - CUSTOM CONFIGURATION")
    print("=" * 80 + "\n")

    # Create custom configuration
    config = RefactronConfig(
        max_function_complexity=5,  # More strict
        max_parameters=3,  # Fewer parameters allowed
        show_details=True,
    )

    print("📝 Custom Configuration:")
    print(f"   Max Complexity: {config.max_function_complexity}")
    print(f"   Max Parameters: {config.max_parameters}")
    print(f"   Enabled Analyzers: {', '.join(config.enabled_analyzers)}")

    # Use custom config
    refactron = Refactron(config)

    example_file = Path(__file__).parent / "bad_code_example.py"

    if example_file.exists():
        print(f"\n📂 Analyzing with strict rules: {example_file}")
        result = refactron.analyze(example_file)
        print(f"\n⚠️  Found {result.total_issues} issues with strict rules!")


def main():
    """Run all demos."""
    print("\n🤖 Welcome to Refactron!")
    print("The Intelligent Code Refactoring Transformer\n")

    try:
        # Demo 1: Basic Analysis
        demo_analysis()

        # Demo 2: Refactoring
        demo_refactoring()

        # Demo 3: Custom Config
        demo_custom_config()

        print("\n" + "=" * 80)
        print("✨ Demo Complete!")
        print("=" * 80)
        print("\n💡 Next Steps:")
        print("   1. Try: refactron analyze your_code.py")
        print("   2. Read: QUICKSTART.md")
        print("   3. Explore: examples/")
        print("\n")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
