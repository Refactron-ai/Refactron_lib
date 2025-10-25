# 🚀 Refactron Real-World Examples

This directory contains realistic examples showing how Refactron can improve your code.

## 📁 Examples

### 1. Flask API (`flask_api_example.py`)
**Scenario:** A typical Flask API with security issues, code smells, and technical debt.

**Issues Detected:**
- 🔒 Hardcoded secrets (API keys, passwords)
- 🔴 Security vulnerabilities (`eval`, debug mode)
- 🟡 Too many function parameters
- 🔵 Deep nesting and complexity
- ⚪ Magic numbers
- 📝 Missing docstrings
- 💀 Dead code

**Try it:**
```bash
# Analyze the code
refactron analyze examples/flask_api_example.py --detailed

# Get refactoring suggestions
refactron refactor examples/flask_api_example.py --preview

# Generate a report
refactron report examples/flask_api_example.py -f json -o flask_report.json
```

**Expected output:** 15-20 issues detected across all categories

---

### 2. Data Science Script (`data_science_example.py`)
**Scenario:** Common data science workflow with typical issues.

**Issues Detected:**
- 🔴 Unsafe pickle usage
- 🔴 Using `eval` for configuration
- 🟡 Too many parameters in preprocessing
- 🔵 Complex functions doing too much
- ⚪ Magic numbers in data splitting
- 📝 Missing type hints
- 💀 Unused functions and dead code

**Try it:**
```bash
# Analyze
refactron analyze examples/data_science_example.py

# Focus on security issues
refactron analyze examples/data_science_example.py --detailed | grep -A 5 "SECURITY"

# Get refactoring suggestions
refactron refactor examples/data_science_example.py --preview -t reduce_parameters
```

**Expected output:** 20-25 issues including critical security warnings

---

### 3. CLI Tool (`cli_tool_example.py`)
**Scenario:** Command-line tool with shell injection and other issues.

**Issues Detected:**
- 🔴 Shell injection vulnerability
- 🔴 Using `eval` on user input
- 🟡 Too many CLI arguments
- 🔵 Deep conditional nesting
- ⚪ Hardcoded magic numbers
- 💀 Dead code and unreachable code

**Try it:**
```bash
# Full analysis
refactron analyze examples/cli_tool_example.py --detailed

# Preview refactoring
refactron refactor examples/cli_tool_example.py --preview

# Get only critical issues
refactron analyze examples/cli_tool_example.py | grep "🔴"
```

**Expected output:** 15-18 issues with critical security concerns

---

## 🎯 Recommended Workflow

### Step 1: Initialize Configuration
```bash
cd examples/
refactron init
```

This creates `.refactron.yaml` with default settings.

### Step 2: Analyze All Examples
```bash
refactron analyze . --summary
```

### Step 3: Get Detailed Report
```bash
refactron report . -f json -o detailed_report.json
```

### Step 4: Preview Refactoring
```bash
refactron refactor flask_api_example.py --preview
```

### Step 5: Apply Safe Refactorings
For low-risk refactorings (like adding docstrings), you could:
1. Review the suggestions
2. Apply them manually
3. Test your code
4. Commit changes

---

## 📊 Expected Analysis Summary

When you run `refactron analyze .` on all examples:

```
📊 Analysis Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files Analyzed: 3
Total Issues: 50-60

By Severity:
  🔴 CRITICAL: 12-15 (security vulnerabilities)
  🟡 WARNING:  15-20 (code smells, parameters)
  🔵 INFO:     20-25 (style, docstrings)

By Category:
  SECURITY:    12-15 issues
  CODE_SMELL:  15-20 issues
  COMPLEXITY:  8-10 issues
  TYPE_HINTS:  10-15 issues
  DEAD_CODE:   5-8 issues
```

---

## 🔧 Common Fixes Suggested

### Magic Numbers → Constants
**Before:**
```python
if amount > 1000:
    return amount * 0.15
```

**After:**
```python
LARGE_ORDER_THRESHOLD = 1000
LARGE_ORDER_DISCOUNT = 0.15

if amount > LARGE_ORDER_THRESHOLD:
    return amount * LARGE_ORDER_DISCOUNT
```

### Too Many Parameters → Config Object
**Before:**
```python
def process(a, b, c, d, e, f):
    return a + b + c + d + e + f
```

**After:**
```python
@dataclass
class ProcessConfig:
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float

def process(config: ProcessConfig):
    return config.a + config.b + config.c + config.d + config.e + config.f
```

### Deep Nesting → Guard Clauses
**Before:**
```python
def process(data):
    if data:
        if data.valid:
            if data.user:
                return data.user.process()
    return None
```

**After:**
```python
def process(data):
    if not data:
        return None
    if not data.valid:
        return None
    if not data.user:
        return None
    
    return data.user.process()
```

---

## 🎓 Learning Points

1. **Security First**: Refactron catches dangerous patterns like `eval()`, `exec()`, shell injection
2. **Code Quality**: Identifies complexity, code smells, and maintainability issues
3. **Type Safety**: Detects missing type hints
4. **Dead Code**: Finds unused functions and unreachable code
5. **Best Practices**: Suggests modern Python patterns

---

## 📚 Next Steps

1. **Try on your own code:**
   ```bash
   refactron analyze /path/to/your/project
   ```

2. **Customize rules:**
   Edit `.refactron.yaml` to adjust thresholds

3. **Integrate into CI/CD:**
   Add Refactron to your testing pipeline

4. **Explore Phase 3 features** (coming soon):
   - AI-powered refactoring
   - Auto-fix capabilities
   - IDE integration

---

## 💡 Tips

- Start with `--summary` for a quick overview
- Use `--detailed` to see all issues
- Try `--preview` before making any changes
- Generate reports in JSON for further processing
- Adjust thresholds in `.refactron.yaml` to match your team's standards

---

**Want to see the difference?** Compare the examples with their refactored versions in the `refactored/` directory (coming soon)!

