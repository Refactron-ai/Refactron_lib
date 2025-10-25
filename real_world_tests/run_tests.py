#!/usr/bin/env python3
"""
Run Refactron on real-world projects.

Tests:
1. Refactron itself (dogfooding)
2. Example projects
3. Test suite
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from real_world_tests.test_runner import RealWorldTester


def main():
    """Run all real-world tests."""
    tester = RealWorldTester()
    reports = []
    
    print("\n" + "="*60)
    print("🏗️  REFACTRON REAL-WORLD TESTING")
    print("="*60)
    print("\nTesting Refactron on actual Python codebases...")
    
    base_path = Path(__file__).parent.parent
    
    # Define test projects
    test_projects = [
        (base_path / "refactron" / "analyzers", "Refactron Analyzers"),
        (base_path / "refactron" / "refactorers", "Refactron Refactorers"),
        (base_path / "refactron" / "core", "Refactron Core"),
        (base_path / "examples", "Example Projects"),
        (base_path / "tests", "Test Suite"),
    ]
    
    # Run tests
    for project_path, project_name in test_projects:
        if not project_path.exists():
            print(f"\n⚠️  Skipping {project_name}: Path not found")
            continue
        
        try:
            report = tester.analyze_project(project_path, project_name)
            reports.append(report)
            tester.save_report(report)
        except Exception as e:
            print(f"❌ Failed to analyze {project_name}: {e}")
    
    # Generate summary
    if reports:
        print("\n" + "="*60)
        print("📊 Generating Summary Report")
        print("="*60)
        
        markdown = tester.generate_markdown_report(reports)
        summary_path = tester.output_dir / "SUMMARY.md"
        summary_path.write_text(markdown)
        
        print(f"\n✅ Summary report: {summary_path}")
        print(f"\n🎉 Testing complete! Analyzed {len(reports)} project(s)")
        
        # Print quick stats
        total_issues = sum(r['summary']['total_issues'] for r in reports if r['status'] == 'success')
        total_critical = sum(r['summary']['critical'] for r in reports if r['status'] == 'success')
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Issues: {total_issues}")
        print(f"   Critical Issues: {total_critical}")
        
        if total_critical > 0:
            print(f"\n⚠️  Found {total_critical} critical issue(s) that should be addressed!")
        else:
            print(f"\n✨ No critical issues found! Great job!")


if __name__ == "__main__":
    main()

