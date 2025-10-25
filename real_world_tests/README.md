# Real-World Testing Suite

This directory contains tools for testing Refactron on actual Python codebases.

## Purpose

These tests are designed for:
- **Manual testing** during development
- **Dogfooding** - testing Refactron on itself
- **Performance benchmarking** on real code
- **Quality validation** before releases

## Files

- `test_runner.py` - Core testing infrastructure
- `run_tests.py` - Main test execution script
- `results/` - Generated test reports (JSON + Markdown)

## Usage

### Run Full Test Suite

```bash
# From project root
python real_world_tests/run_tests.py
```

This will analyze:
- Refactron's own codebase (analyzers, refactorers, core)
- Example projects
- Test suite

### Custom Testing

```python
from pathlib import Path
from real_world_tests.test_runner import RealWorldTester

tester = RealWorldTester()
report = tester.analyze_project(Path("your/project"), "Your Project")
tester.save_report(report)
```

## Output

Results are saved to `real_world_tests/results/`:
- `{project_name}_report.json` - Detailed JSON report for each project
- `SUMMARY.md` - Markdown summary of all tests

## CI/CD Note

⚠️ **These tests are NOT run in GitHub Actions CI/CD**

The CI pipeline uses simpler integration tests defined in `.github/workflows/ci.yml` that:
- Test CLI commands
- Verify package installation
- Check Python API imports

This real-world testing suite is meant for:
- Local development and validation
- Pre-release quality checks
- Performance profiling
- Manual QA

## Example Output

```
============================================================
📊 Analyzing: Refactron Core
============================================================
📁 Files: 6
📝 Lines: 547

✅ Analysis Complete!
⏱️  Time: 1.23s
🔍 Issues Found: 12
   🔴 Critical: 0
   ⚡ Warnings: 8
   ℹ️  Info: 4

📈 Metrics:
   Issues per file: 2.00
   Issues per 1K lines: 21.94
```

## Maintenance

When adding new Refactron features:
1. Run this test suite locally
2. Review the generated reports
3. Update expectations if needed
4. Check for performance regressions

