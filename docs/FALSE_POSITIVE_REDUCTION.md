# False Positive Reduction Features

This document describes the false positive reduction features implemented in the Refactron security analyzer.

## Overview

The security analyzer now includes several mechanisms to reduce false positives:

1. **Confidence Scores** - Each issue has a confidence score (0.0-1.0)
2. **Context Awareness** - Different confidence levels based on file context (test files, examples, etc.)
3. **Whitelist/Ignore Mechanisms** - Ability to whitelist rules for specific file patterns
4. **Minimum Confidence Filtering** - Filter out low confidence issues
5. **False Positive Tracking** - System to learn from false positives

## Confidence Scores

All security issues now include a `confidence` field ranging from 0.0 (low confidence) to 1.0 (high confidence). This helps users understand how certain the analyzer is about each finding.

### Confidence Levels by Rule

- **SEC001** (dangerous functions like eval, exec): 0.6 in test files, 1.0 elsewhere
- **SEC002** (dangerous imports): 0.6 in test files, 1.0 elsewhere
- **SEC003** (hardcoded secrets): 0.5 in test/example files, 0.8 elsewhere
- **SEC004** (SQL injection): 0.9
- **SEC005** (command injection): 0.95
- **SEC006** (weak crypto): 0.85
- **SEC007** (unsafe YAML): 0.95
- **SEC008** (assert statements): 0.6 (context-dependent)
- **SEC009** (SQL parameterization): 0.85-0.9
- **SEC010** (SSRF): 0.75
- **SEC011** (insecure random): 0.49-0.7 (lower in test files)
- **SEC012-SEC013** (weak SSL/TLS): 0.95

## Context Awareness

The analyzer automatically adjusts confidence based on file context:

### Test Files
Files matching patterns like `test_*.py`, `*_test.py`, or in `tests/` directories:
- Get 60% confidence multiplier for rules SEC001, SEC002, SEC011
- This reduces false positives for legitimate test code using `eval()`, `pickle`, or `random`

### Example/Demo Files
Files in paths containing `example`, `demo`, `sample`, or `tutorial`:
- Get 70% confidence multiplier for rules SEC001, SEC002, SEC011
- Acknowledges that demo code may not follow production security practices

### Hardcoded Secrets
Hardcoded secrets detection uses lower confidence (0.5) in test/example files:
- Test API keys like `"test-api-key-12345"` are often acceptable in tests
- Production files maintain 0.8 confidence for better detection

## Configuration

### Ignore Patterns

Configure which files to completely ignore for security analysis:

```yaml
# .refactron.yaml
security_ignore_patterns:
  - "**/test_*.py"
  - "**/tests/**/*.py"
  - "**/*_test.py"
```

This is useful for:
- Test files that intentionally use dangerous functions
- Generated code
- Third-party code in your repository

### Rule Whitelisting

Whitelist specific rules for certain file patterns:

```yaml
security_rule_whitelist:
  SEC001:  # Allow eval() in test files
    - "**/test_*.py"
    - "**/tests/**/*.py"
  SEC011:  # Allow random module in examples
    - "**/examples/**/*.py"
    - "**/demos/**/*.py"
  SEC002:  # Allow pickle in specific files
    - "**/serialization.py"
```

This allows fine-grained control over which rules apply where.

### Minimum Confidence

Set a minimum confidence threshold to filter low-confidence issues:

```yaml
security_min_confidence: 0.7  # Only show issues with confidence >= 0.7
```

Default is 0.5. Recommended values:
- **0.5** (default): Balanced - shows most issues
- **0.7**: Stricter - focuses on higher confidence issues
- **0.9**: Very strict - only very high confidence issues

## False Positive Tracker

The `FalsePositiveTracker` class provides a learning mechanism:

### Basic Usage

```python
from pathlib import Path
from refactron.core.false_positive_tracker import FalsePositiveTracker

# Create tracker (stores in ~/.refactron/false_positives.json by default)
tracker = FalsePositiveTracker()

# Mark a pattern as false positive
tracker.mark_false_positive("SEC001", "eval() in test helper")

# Check if a pattern is a known false positive
if tracker.is_false_positive("SEC001", "eval() in test helper"):
    print("Known false positive, can be ignored")

# Get all false positive patterns for a rule
patterns = tracker.get_false_positive_patterns("SEC001")

# Clear false positives for a specific rule
tracker.clear_rule("SEC001")

# Clear all false positives
tracker.clear_all()
```

### Custom Storage Location

```python
tracker = FalsePositiveTracker(Path("/custom/path/fp.json"))
```

### Integration with Analyzers

While the tracker is available, it's not automatically integrated with the analyzer. You can use it in your workflow:

```python
from refactron.analyzers.security_analyzer import SecurityAnalyzer
from refactron.core.config import RefactronConfig
from refactron.core.false_positive_tracker import FalsePositiveTracker

config = RefactronConfig()
analyzer = SecurityAnalyzer(config)
tracker = FalsePositiveTracker()

# Analyze code
issues = analyzer.analyze(Path("myfile.py"), code)

# Filter out known false positives
filtered_issues = []
for issue in issues:
    pattern = f"{issue.message} at {issue.file_path}:{issue.line_number}"
    if not tracker.is_false_positive(issue.rule_id, pattern):
        filtered_issues.append(issue)
    else:
        print(f"Skipping known false positive: {pattern}")
```

## Examples

### Example 1: Test File with eval()

```python
# tests/test_calculator.py
def test_eval_expression():
    result = eval("2 + 2")  # Would be SEC001 with 0.6 confidence
    assert result == 4
```

With default config (min_confidence=0.5), this would be reported but with lower confidence.
With min_confidence=0.7, this would be filtered out.

### Example 2: Whitelisting pickle in Serialization Module

```yaml
# .refactron.yaml
security_rule_whitelist:
  SEC002:
    - "**/serialization.py"
```

```python
# myapp/serialization.py
import pickle  # SEC002 - but whitelisted for this file

def serialize(obj):
    return pickle.dumps(obj)
```

### Example 3: Combining Features

```yaml
# .refactron.yaml
security_ignore_patterns:
  - "**/test_*.py"
  - "**/tests/**/*.py"

security_rule_whitelist:
  SEC011:
    - "**/examples/**"

security_min_confidence: 0.7
```

This configuration:
- Ignores all test files completely
- Allows `random` module in examples
- Only reports issues with 70%+ confidence

## Best Practices

1. **Start with defaults** - The default configuration (min_confidence=0.5, test files ignored) is a good starting point

2. **Gradually tune** - If you get too many false positives:
   - Increase `security_min_confidence` to 0.6 or 0.7
   - Add specific file patterns to `security_rule_whitelist`
   - Use `security_ignore_patterns` for generated or third-party code

3. **Don't over-whitelist** - Be careful not to whitelist security rules too broadly:
   - ✅ Good: Whitelist SEC001 for specific test files
   - ❌ Bad: Whitelist SEC001 for all files

4. **Review low confidence issues** - Even if filtered, review low confidence issues periodically:
   - They might indicate real problems
   - Help train the false positive tracker

5. **Use false positive tracker** - Build a knowledge base of known false positives:
   - Speeds up future analysis
   - Helps team consistency
   - Can be shared across projects

## Migration Guide

If you're upgrading from a previous version:

1. **Confidence scores are automatic** - All existing code continues to work, issues now have a `confidence` field

2. **Default behavior changed for test files** - Test files are now ignored by default. To restore old behavior:
   ```yaml
   security_ignore_patterns: []
   ```

3. **Low confidence issues may be hidden** - With min_confidence=0.5, some issues that were previously shown (like assert statements) may now be filtered. To see all issues:
   ```yaml
   security_min_confidence: 0.0
   ```

## API Reference

### RefactronConfig

New fields:
- `security_ignore_patterns: List[str]` - File patterns to ignore
- `security_rule_whitelist: Dict[str, List[str]]` - Rule whitelist by file pattern
- `security_min_confidence: float` - Minimum confidence threshold (default: 0.5)

### CodeIssue

New field:
- `confidence: float` - Confidence score 0.0-1.0 (default: 1.0)

### FalsePositiveTracker

Methods:
- `mark_false_positive(rule_id: str, pattern: str)` - Mark a pattern as false positive
- `is_false_positive(rule_id: str, pattern: str) -> bool` - Check if pattern is false positive
- `get_false_positive_patterns(rule_id: str) -> List[str]` - Get all patterns for a rule
- `clear_rule(rule_id: str)` - Clear false positives for a rule
- `clear_all()` - Clear all false positives
