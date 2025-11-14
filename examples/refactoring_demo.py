#!/usr/bin/env python3
"""
Refactoring Demo - Shows Concrete Code Suggestions

This demo showcases Refactron's ability to generate actual refactored code.
"""

from pathlib import Path

from refactron import Refactron


def main():
    print("\n" + "=" * 80)
    print("🔧 REFACTRON - REFACTORING SUGGESTIONS DEMO")
    print("=" * 80)
    print("\nRefactron doesn't just find issues - it shows you the EXACT refactored code!")
    print("\n" + "-" * 80)

    # Initialize Refactron
    refactron = Refactron()

    # Analyze the bad code example
    example_file = Path(__file__).parent / "bad_code_example.py"

    if not example_file.exists():
        print("❌ Example file not found!")
        return

    print(f"\n📂 Analyzing: {example_file.name}")
    print("\nGenerating refactoring suggestions...\n")

    # Get refactoring suggestions
    result = refactron.refactor(example_file, preview=True)

    if not result.operations:
        print("✅ No refactoring suggestions - code looks good!")
        return

    print(f"✨ Found {result.total_operations} refactoring opportunities!\n")
    print("=" * 80)

    # Show a few specific examples
    print("\n📝 EXAMPLE 1: Extract Magic Numbers to Constants")
    print("-" * 80)

    extract_constant_ops = result.operations_by_type("extract_constant")
    if extract_constant_ops:
        op = extract_constant_ops[0]
        print(f"📍 Location: Line {op.line_number}")
        print(f"💡 Description: {op.description}")
        print(f"🎯 Risk Score: {op.risk_score:.2f} (0.0 = Safe, 1.0 = Risky)")
        print(f"\n💭 Reasoning:\n   {op.reasoning}\n")

        print("❌ BEFORE:")
        for line in op.old_code.split("\n")[:8]:
            print(f"   {line}")

        print("\n✅ AFTER:")
        for line in op.new_code.split("\n")[:12]:
            print(f"   {line}")

    # Show parameter reduction example
    print("\n\n📝 EXAMPLE 2: Reduce Parameters with Config Object")
    print("-" * 80)

    reduce_params_ops = result.operations_by_type("reduce_parameters")
    if reduce_params_ops:
        op = reduce_params_ops[0]
        print(f"📍 Location: Line {op.line_number}")
        print(f"💡 Description: {op.description}")
        print(f"🎯 Risk Score: {op.risk_score:.2f}")
        print(f"\n💭 Reasoning:\n   {op.reasoning}\n")

        print("❌ BEFORE:")
        for line in op.old_code.split("\n")[:4]:
            print(f"   {line}")

        print("\n✅ AFTER (showing config class):")
        for line in op.new_code.split("\n")[2:10]:
            print(f"   {line}")

    # Show simplify conditionals
    print("\n\n📝 EXAMPLE 3: Simplify Nested Conditionals")
    print("-" * 80)

    simplify_ops = result.operations_by_type("simplify_conditionals")
    if simplify_ops:
        op = simplify_ops[0]
        print(f"📍 Location: Line {op.line_number}")
        print(f"💡 Description: {op.description}")
        print(f"🎯 Risk Score: {op.risk_score:.2f}")
        print(f"\n💭 Reasoning:\n   {op.reasoning}\n")

        print("✅ SUGGESTED PATTERN:")
        for line in op.new_code.split("\n")[:10]:
            print(f"   {line}")

    # Show add docstring
    print("\n\n📝 EXAMPLE 4: Add Missing Docstrings")
    print("-" * 80)

    docstring_ops = result.operations_by_type("add_docstring")
    if docstring_ops:
        op = docstring_ops[0]
        print(f"📍 Location: Line {op.line_number}")
        print(f"💡 Description: {op.description}")
        print(f"🎯 Risk Score: {op.risk_score:.2f} (Very Safe!)")
        print(f"\n💭 Reasoning:\n   {op.reasoning}\n")

        print("❌ BEFORE:")
        for line in op.old_code.split("\n")[:3]:
            print(f"   {line}")

        print("\n✅ AFTER:")
        for line in op.new_code.split("\n")[:8]:
            print(f"   {line}")

    # Summary by type
    print("\n\n📊 SUMMARY BY REFACTORING TYPE")
    print("=" * 80)

    refactoring_types = {
        "extract_constant": "Extract Magic Numbers to Constants",
        "simplify_conditionals": "Simplify Nested Conditionals",
        "reduce_parameters": "Reduce Function Parameters",
        "add_docstring": "Add Missing Docstrings",
        "extract_method": "Extract Methods",
    }

    for op_type, description in refactoring_types.items():
        ops = result.operations_by_type(op_type)
        if ops:
            avg_risk = sum(op.risk_score for op in ops) / len(ops)
            print(f"✓ {description:40} : {len(ops):2} suggestions (avg risk: {avg_risk:.2f})")

    # Risk breakdown
    print("\n🛡️  RISK BREAKDOWN")
    print("=" * 80)
    print(f"✅ Safe Operations (risk ≤ 0.3):      {len(result.safe_operations)}")
    moderate_count = (
        result.total_operations - len(result.safe_operations) - len(result.high_risk_operations)
    )
    print(f"⚠️  Moderate Risk (0.3 < risk ≤ 0.7): {moderate_count}")
    print(f"🔴 High Risk (risk > 0.7):           {len(result.high_risk_operations)}")

    print("\n" + "=" * 80)
    print("🎯 WHAT THIS MEANS FOR YOU")
    print("=" * 80)
    print(
        """
Refactron provides:

1. 🔍 Detection - Finds code issues automatically
2. 💡 Suggestions - Explains WHY something should change
3. ✨ Concrete Code - Shows you EXACTLY how to fix it
4. 🛡️  Risk Scoring - Tells you how safe each change is
5. 📝 Context - Provides reasoning for each suggestion

You can:
- Copy/paste the suggested code
- Learn better patterns
- Apply changes selectively
- Share suggestions with your team
- Use in code reviews
"""
    )

    print("=" * 80)
    print("💡 TIP: Run 'refactron refactor <file> --preview' anytime!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
