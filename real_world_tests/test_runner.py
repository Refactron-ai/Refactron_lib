"""
Real-world test runner for Refactron.

This script analyzes actual Python projects and generates detailed reports.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from refactron import Refactron
from refactron.core.config import RefactronConfig


class RealWorldTester:
    """Test Refactron on real-world projects."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("real_world_tests/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = RefactronConfig.default()
        self.refactron = Refactron(self.config)

    def analyze_project(self, project_path: Path, project_name: str) -> Dict[str, Any]:
        """Analyze a single project and return results."""
        print(f"\n{'='*60}")
        print(f"📊 Analyzing: {project_name}")
        print(f"{'='*60}")

        start_time = time.time()

        # Count Python files
        py_files = list(project_path.rglob("*.py"))
        total_lines = 0
        for py_file in py_files:
            try:
                total_lines += len(py_file.read_text().splitlines())
            except Exception:
                pass

        print(f"📁 Files: {len(py_files)}")
        print(f"📝 Lines: {total_lines:,}")

        # Run analysis
        try:
            result = self.refactron.analyze(str(project_path))
            analysis_time = time.time() - start_time

            summary = result.summary()

            # Categorize issues by type
            issues_by_category: Dict[str, List[Dict[str, Any]]] = {}
            for issue in result.all_issues:
                category = issue.category.value
                if category not in issues_by_category:
                    issues_by_category[category] = []
                issues_by_category[category].append(
                    {
                        "file": str(issue.file_path),
                        "line": issue.line_number,
                        "level": issue.level.value,
                        "message": issue.message,
                    }
                )

            # Calculate metrics
            issues_per_file = summary["total_issues"] / max(len(py_files), 1)
            issues_per_1000_lines = (summary["total_issues"] / max(total_lines, 1)) * 1000

            report = {
                "project_name": project_name,
                "project_path": str(project_path),
                "timestamp": datetime.now().isoformat(),
                "analysis_time": f"{analysis_time:.2f}s",
                "files_analyzed": len(py_files),
                "total_lines": total_lines,
                "summary": summary,
                "issues_by_category": issues_by_category,
                "metrics": {
                    "issues_per_file": round(issues_per_file, 2),
                    "issues_per_1000_lines": round(issues_per_1000_lines, 2),
                },
                "status": "success",
            }

            # Print summary
            print("\n✅ Analysis Complete!")
            print(f"⏱️  Time: {analysis_time:.2f}s")
            print(f"🔍 Issues Found: {summary['total_issues']}")
            print(f"   🔴 Critical: {summary['critical']}")
            print(f"   ⚡ Warnings: {summary['warnings']}")
            print(f"   ℹ️  Info: {summary['info']}")
            print("\n📈 Metrics:")
            print(f"   Issues per file: {issues_per_file:.2f}")
            print(f"   Issues per 1K lines: {issues_per_1000_lines:.2f}")

            if issues_by_category:
                print("\n📊 Issues by Category:")
                for category, issues in sorted(
                    issues_by_category.items(), key=lambda x: len(x[1]), reverse=True
                ):
                    print(f"   {category}: {len(issues)}")

            return report

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {
                "project_name": project_name,
                "project_path": str(project_path),
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e),
            }

    def save_report(self, report: Dict[str, Any]):
        """Save report to JSON file."""
        project_name = report["project_name"].replace(" ", "_").lower()
        filename = f"{project_name}_report.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Report saved: {filepath}")
        return filepath

    def generate_markdown_report(self, reports: list) -> str:
        """Generate a markdown summary of all tests."""
        md = "# 🏗️ Refactron Real-World Testing Results\n\n"
        md += f"**Date:** {datetime.now().strftime('%B %d, %Y')}\n\n"
        md += "---\n\n"

        # Summary table
        md += "## 📊 Summary\n\n"
        md += "| Project | Files | Lines | Issues | Critical | Time |\n"
        md += "|---------|-------|-------|--------|----------|------|\n"

        total_files = 0
        total_lines = 0
        total_issues = 0
        total_critical = 0

        for report in reports:
            if report["status"] == "success":
                summary = report["summary"]
                md += f"| {report['project_name']} "
                md += f"| {report['files_analyzed']} "
                md += f"| {report['total_lines']:,} "
                md += f"| {summary['total_issues']} "
                md += f"| {summary['critical']} "
                md += f"| {report['analysis_time']} |\n"

                total_files += report["files_analyzed"]
                total_lines += report["total_lines"]
                total_issues += summary["total_issues"]
                total_critical += summary["critical"]

        md += (
            f"| **TOTAL** | **{total_files}** | **{total_lines:,}** | "
            f"**{total_issues}** | **{total_critical}** | - |\n\n"
        )

        # Individual project details
        md += "---\n\n"
        md += "## 📝 Detailed Reports\n\n"

        for report in reports:
            if report["status"] != "success":
                continue

            md += f"### {report['project_name']}\n\n"
            md += f"**Path:** `{report['project_path']}`\n\n"

            summary = report["summary"]
            metrics = report["metrics"]

            md += "**Statistics:**\n"
            md += f"- Files: {report['files_analyzed']}\n"
            md += f"- Lines: {report['total_lines']:,}\n"
            md += f"- Analysis Time: {report['analysis_time']}\n\n"

            md += "**Issues Found:**\n"
            md += f"- 🔴 Critical: {summary['critical']}\n"
            md += f"- ⚡ Warnings: {summary['warnings']}\n"
            md += f"- ℹ️  Info: {summary['info']}\n"
            md += f"- **Total:** {summary['total_issues']}\n\n"

            md += "**Quality Metrics:**\n"
            md += f"- Issues per file: {metrics['issues_per_file']}\n"
            md += f"- Issues per 1,000 lines: {metrics['issues_per_1000_lines']}\n\n"

            if report["issues_by_category"]:
                md += "**Issues by Category:**\n"
                for category, issues in sorted(
                    report["issues_by_category"].items(), key=lambda x: len(x[1]), reverse=True
                ):
                    md += f"- `{category}`: {len(issues)}\n"
                md += "\n"

            md += "---\n\n"

        # Insights
        md += "## 💡 Key Insights\n\n"

        if reports:
            avg_issues_per_file = total_issues / max(total_files, 1)
            avg_issues_per_1k = (total_issues / max(total_lines, 1)) * 1000

            md += f"1. **Average Issues per File:** {avg_issues_per_file:.2f}\n"
            md += f"2. **Average Issues per 1,000 Lines:** {avg_issues_per_1k:.2f}\n"
            md += f"3. **Total Critical Issues Found:** {total_critical}\n"
            md += f"4. **Total Projects Analyzed:** {len(reports)}\n\n"

        md += "---\n\n"
        md += "**Generated by Refactron Real-World Testing Suite**\n"

        return md


def main():
    """Main test runner."""
    tester = RealWorldTester()
    reports = []

    print("\n" + "=" * 60)
    print("🏗️  REFACTRON REAL-WORLD TESTING")
    print("=" * 60)

    # Test projects (will be defined in the main script)
    test_projects = [
        # Will be populated dynamically
    ]

    if not test_projects:
        print("\n⚠️  No test projects defined. Add projects to analyze.")
        return

    # Run tests
    for project_path, project_name in test_projects:
        if not project_path.exists():
            print(f"\n⚠️  Skipping {project_name}: Path not found")
            continue

        report = tester.analyze_project(project_path, project_name)
        reports.append(report)
        tester.save_report(report)

    # Generate summary
    if reports:
        print("\n" + "=" * 60)
        print("📊 Generating Summary Report")
        print("=" * 60)

        markdown = tester.generate_markdown_report(reports)
        summary_path = tester.output_dir / "SUMMARY.md"
        summary_path.write_text(markdown)

        print(f"\n✅ Summary report: {summary_path}")
        print(f"\n🎉 Testing complete! Analyzed {len(reports)} project(s)")


if __name__ == "__main__":
    main()
