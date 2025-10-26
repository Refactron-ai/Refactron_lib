# 🎯 Manual CLI Testing Commands

Complete guide for testing all Refactron CLI commands.

---

## 📋 Test Files Created

- `manual_test_bad.py` - File with intentional issues
- `manual_test_good.py` - Clean reference file

---

## 🔍 1. ANALYZE Command

### Basic Analysis
```bash
# Analyze single file
refactron analyze manual_test_bad.py

# Analyze with detailed output
refactron analyze manual_test_bad.py --detailed

# Analyze directory
refactron analyze examples/

# Analyze with summary only
refactron analyze manual_test_bad.py --summary
```

### With Configuration
```bash
# Use custom config
refactron analyze manual_test_bad.py --config .refactron.yaml

# Create config first
refactron init
# Then analyze
refactron analyze manual_test_bad.py --config .refactron.yaml
```

---

## 🔧 2. REFACTOR Command

### Preview Mode (Safe)
```bash
# Preview refactoring suggestions
refactron refactor manual_test_bad.py --preview

# Preview specific refactoring types
refactron refactor manual_test_bad.py --preview -t extract_constant
refactron refactor manual_test_bad.py --preview -t add_docstring

# Preview multiple types
refactron refactor manual_test_bad.py --preview -t extract_constant -t add_docstring
```

### Apply Mode (Makes Changes)
```bash
# Apply all refactorings
refactron refactor manual_test_bad.py --apply

# Apply specific types only
refactron refactor manual_test_bad.py --apply -t extract_constant
```

---

## 🤖 3. AUTOFIX Command (NEW - Phase 3)

### Preview Fixes
```bash
# Preview available fixers
refactron autofix manual_test_bad.py --preview

# Preview with different safety levels
refactron autofix manual_test_bad.py --preview --safety-level safe
refactron autofix manual_test_bad.py --preview --safety-level low
refactron autofix manual_test_bad.py --preview --safety-level moderate
refactron autofix manual_test_bad.py --preview --safety-level high
```

### Apply Fixes
```bash
# Apply fixes (creates backup automatically)
refactron autofix manual_test_bad.py --apply

# Apply with moderate safety level
refactron autofix manual_test_bad.py --apply --safety-level moderate

# Apply to directory
refactron autofix examples/ --apply --safety-level safe
```

### Safety Levels Explained
- `safe` (0.0) - Only 100% safe fixes (remove whitespace, sort imports)
- `low` (0.2) - Low-risk fixes (extract constants, add docstrings)
- `moderate` (0.4) - Some risk (boolean simplification, f-strings)
- `high` (0.6+) - Higher risk (type hints, complex refactoring)

---

## 📊 4. REPORT Command

### Generate Reports
```bash
# Text report to stdout
refactron report manual_test_bad.py

# JSON report
refactron report manual_test_bad.py --format json

# HTML report
refactron report manual_test_bad.py --format html

# Save to file
refactron report manual_test_bad.py --format json -o report.json
refactron report manual_test_bad.py --format html -o report.html
```

### Report Options
```bash
# Report with custom config
refactron report manual_test_bad.py --config .refactron.yaml --format json
```

---

## ⚙️ 5. INIT Command

### Initialize Configuration
```bash
# Create default config
refactron init

# Check created file
cat .refactron.yaml

# Create config in custom location
refactron init --path my-config.yaml
```

---

## 🧪 Complete Test Workflow

### Workflow 1: Analyze → Autofix
```bash
# Step 1: Analyze to find issues
refactron analyze manual_test_bad.py --detailed

# Step 2: Preview auto-fixes
refactron autofix manual_test_bad.py --preview

# Step 3: Apply safe fixes
refactron autofix manual_test_bad.py --apply --safety-level safe

# Step 4: Check if issues are fixed
refactron analyze manual_test_bad.py
```

### Workflow 2: Full Pipeline
```bash
# 1. Create config
refactron init

# 2. Analyze
refactron analyze manual_test_bad.py --config .refactron.yaml --detailed

# 3. Generate report
refactron report manual_test_bad.py --format json -o before.json

# 4. Auto-fix
refactron autofix manual_test_bad.py --apply --safety-level moderate

# 5. Re-analyze
refactron analyze manual_test_bad.py

# 6. Generate after report
refactron report manual_test_bad.py --format json -o after.json

# 7. Compare
diff before.json after.json
```

### Workflow 3: Backup & Rollback
```bash
# 1. Apply fixes (auto-creates backup)
refactron autofix manual_test_bad.py --apply

# 2. Check backup directory
ls -la .refactron_backups/

# 3. View backup index
cat .refactron_backups/index.json

# 4. If you don't like changes, restore from backup
cp .refactron_backups/*.bak manual_test_bad.py
```

---

## 🎨 Visual Output Examples

### Analyze Output
```
🔍 Refactron Analysis

     Analysis Summary     
┏━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric         ┃ Value ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Files Analyzed │     1 │
│ Total Issues   │    15 │
│ 🔴 Critical    │     2 │
│ ❌ Errors      │     3 │
│ ⚡ Warnings    │     8 │
│ ℹ️  Info        │     2 │
└────────────────┴───────┘
```

### Autofix Output
```
🔧 Refactron Auto-fix

📋 Preview mode: No changes will be applied

🛡️  Safety level: safe
🔧 Available fixers: 14

Available Auto-fixes:

🟢 remove_unused_imports (risk: 0.0)
🟢 sort_imports (risk: 0.0)
🟢 remove_trailing_whitespace (risk: 0.0)
🟡 normalize_quotes (risk: 0.1)
🟡 simplify_boolean (risk: 0.3)
...
```

---

## 🔍 Testing Individual Fixers

### Test Each Fixer
```bash
# Each fixer can be tested by creating specific issues:

# 1. Unused imports
echo "import os\nimport sys\n\nprint('hello')" > test_imports.py
refactron autofix test_imports.py --preview

# 2. Trailing whitespace
echo "x = 1   \ny = 2   " > test_whitespace.py
refactron autofix test_whitespace.py --preview

# 3. Boolean simplification
echo "if x == True:\n    pass" > test_boolean.py
refactron autofix test_boolean.py --preview

# 4. Format strings
echo 'print("Hello {}".format(name))' > test_format.py
refactron autofix test_format.py --preview

# 5. Indentation
printf "def test():\n\treturn 1" > test_indent.py
refactron autofix test_indent.py --preview
```

---

## ⚡ Quick Tests

### 1-Minute Smoke Test
```bash
# Test all commands quickly
refactron --version
refactron analyze manual_test_bad.py
refactron refactor manual_test_bad.py --preview
refactron autofix manual_test_bad.py --preview
refactron report manual_test_bad.py
refactron init
```

### 5-Minute Full Test
```bash
# Complete test sequence
refactron init
refactron analyze manual_test_bad.py --detailed
refactron report manual_test_bad.py --format json -o report.json
refactron refactor manual_test_bad.py --preview -t extract_constant
refactron autofix manual_test_bad.py --preview
refactron autofix manual_test_bad.py --apply --safety-level moderate
refactron analyze manual_test_bad.py  # Should show fewer issues
```

---

## 🐛 Error Testing

### Test Error Handling
```bash
# Non-existent file
refactron analyze nonexistent.py
# Should show: "Error: Path does not exist"

# Invalid config
refactron analyze manual_test_bad.py --config invalid.yaml
# Should show: "Error loading configuration"

# Invalid safety level
refactron autofix manual_test_bad.py --safety-level invalid
# Should show help for valid options
```

---

## 📊 Performance Testing

### Test on Large Projects
```bash
# Analyze entire project
refactron analyze refactron/ --detailed

# Analyze examples directory
refactron analyze examples/ --detailed

# Generate full project report
refactron report refactron/ --format json -o full_report.json
```

---

## ✅ Verification Checklist

After running commands, verify:

- [ ] `analyze` shows issues correctly
- [ ] `refactor --preview` shows suggestions
- [ ] `autofix --preview` lists 14 fixers
- [ ] `autofix --apply` creates backup
- [ ] Backup exists in `.refactron_backups/`
- [ ] `report` generates files correctly
- [ ] `init` creates `.refactron.yaml`
- [ ] Error messages are helpful
- [ ] Colors/formatting work in terminal
- [ ] File operations are safe (no data loss)

---

## 🎯 Expected Results

### manual_test_bad.py Issues
Should detect:
- ✅ 4 unused imports (os, sys, json, random)
- ✅ Magic number (42)
- ✅ Boolean comparison (x == True)
- ✅ Old format string
- ✅ Unused variable
- ✅ Tab character (indentation)
- ✅ Missing docstrings
- ✅ Trailing whitespace
- ✅ Boolean comparison (value == False)

### After Autofix (moderate level)
Should fix:
- ✅ Remove unused imports
- ✅ Remove trailing whitespace
- ✅ Simplify booleans (x == True → x)
- ✅ Convert to f-strings
- ✅ Fix indentation (tabs → spaces)

---

## 💡 Tips

1. **Always use --preview first** before --apply
2. **Check backups** in `.refactron_backups/`
3. **Start with safe level** then increase if needed
4. **Use detailed mode** for analysis to see all issues
5. **Generate reports** before and after fixes to compare

---

## 🆘 Help Commands

```bash
# Main help
refactron --help

# Command-specific help
refactron analyze --help
refactron refactor --help
refactron autofix --help
refactron report --help
refactron init --help
```

---

**Happy Testing! 🎉**

All commands are ready to use. Start with the 1-minute smoke test, then try the full workflows.

