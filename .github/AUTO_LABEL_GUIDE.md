# 🏷️ Auto-label Bot - Intelligent Labeling Guide

## 📋 **Overview**

The Auto-label Bot automatically adds relevant labels to issues and pull requests based on their content, title, and file changes.

---

## 🎯 **How It Works**

### **For Issues:**
Labels are added based on:
- Title keywords (e.g., "bug", "feature", "question")
- Body content
- Issue description

### **For Pull Requests:**
Labels are added based on:
- PR title and description
- **Changed files** (e.g., `.py` files = code, `.md` files = docs)
- **PR size** (additions + deletions)
- File types

---

## 🏷️ **Available Labels**

### **Issue Labels**

#### **Type Labels:**
- `bug` - Bugs, errors, crashes
- `enhancement` - Feature requests, improvements
- `question` - Questions, how-to's
- `documentation` - Docs, README, guides
- `security` - Security issues, vulnerabilities
- `performance` - Performance issues, optimization
- `testing` - Test-related
- `refactoring` - Code cleanup, refactoring

#### **Community Labels:**
- `good-first-issue` - Beginner-friendly
- `help-wanted` - Community assistance needed

#### **Priority Labels:**
- `priority: high` - Urgent, critical issues
- `priority: medium` - Important issues

---

### **PR Labels**

#### **Type Labels:**
- `bug` - Bug fixes
- `enhancement` - New features
- `documentation` - Docs changes
- `testing` - Test additions/changes
- `refactoring` - Code cleanup
- `performance` - Performance improvements
- `security` - Security fixes
- `dependencies` - Dependency updates
- `ci-cd` - CI/CD changes

#### **Size Labels:**
- `size: small` - < 50 changes
- `size: medium` - 50-199 changes
- `size: large` - 200-499 changes
- `size: x-large` - 500+ changes

---

## 🔍 **Labeling Rules**

### **Bug Detection:**
```
Keywords: bug, error, fix, crash, exception, failure
Example: "Bug: Function returns None incorrectly"
Result: Labeled as "bug"
```

### **Feature Detection:**
```
Keywords: feature, add, enhancement, improve, implement
Example: "Add support for TypeScript"
Result: Labeled as "enhancement"
```

### **Documentation Detection:**
```
Keywords: doc, readme, documentation, guide
Files: *.md, docs/
Example: "Update README with new instructions"
Result: Labeled as "documentation"
```

### **Performance Detection:**
```
Keywords: performance, slow, optimization, faster
Example: "Optimize database queries"
Result: Labeled as "performance"
```

### **Security Detection:**
```
Keywords: security, vulnerability, CVE
Example: "Fix SQL injection vulnerability"
Result: Labeled as "security"
```

### **Good First Issue:**
```
Keywords: simple, easy, beginner, starter
Example: "Simple bug fix for new contributors"
Result: Labeled as "good-first-issue"
```

---

## 📊 **PR Size Detection**

The bot automatically calculates PR size:

| Size | Changes | Label |
|------|---------|-------|
| Small | < 50 | `size: small` |
| Medium | 50-199 | `size: medium` |
| Large | 200-499 | `size: large` |
| X-Large | 500+ | `size: x-large` |

**Example:**
```
PR with 25 additions + 15 deletions = 40 changes
Result: "size: small"
```

---

## 🧪 **Examples**

### **Example 1: Bug Report**
```
Title: "Bug: Function crashes when called with None"
Body: "When I call process_data(None), it raises an exception..."

Labels Applied:
✅ bug
```

### **Example 2: Feature Request**
```
Title: "Feature: Add logging support"
Body: "It would be nice to have built-in logging..."

Labels Applied:
✅ enhancement
```

### **Example 3: Documentation Update PR**
```
Title: "Update API documentation"
Changed Files: docs/api.md, README.md

Labels Applied:
✅ documentation
✅ size: small
```

### **Example 4: Large Code Change PR**
```
Title: "Refactor authentication system"
Changed Files: auth.py, utils.py, tests/test_auth.py
Changes: 300 additions, 150 deletions

Labels Applied:
✅ refactoring
✅ size: large
```

---

## 💡 **Smart Features**

### **Multi-Label Support:**
The bot can add multiple labels to a single issue/PR:

```
Title: "Bug fix: Improve performance of data processing"
Labels Applied:
✅ bug
✅ performance
```

### **File-Based Detection:**
PRs are labeled based on files changed:

```
Changed: refactron/analyzers/security_analyzer.py
Label Applied: (type-based, not auto)

Changed: .github/workflows/ci.yml
Labels Applied:
✅ ci-cd
```

---

## 🚀 **Usage**

### **Automatic Labeling:**
1. **Create an issue** or **open a PR**
2. Bot analyzes the content automatically
3. Labels are added within 30 seconds
4. No action required!

### **Manual Override:**
- You can always **add/remove** labels manually
- Bot won't remove labels you add
- Bot only adds, never removes

---

## 🎯 **Benefits**

✅ **Automated** - No manual label management
✅ **Consistent** - Same rules for everyone
✅ **Fast** - Labels added within seconds
✅ **Smart** - Keyword and file-based detection
✅ **Helpful** - Helps organize issues/PRs
✅ **Free** - No external services needed

---

## 🔧 **Customization**

Want to add more labels or keywords? Edit:

`.github/workflows/auto-label.yml`

Just add new conditions:

```javascript
// Example: Add "documentation" label for guide keywords
if (title.includes('guide') || body.includes('tutorial')) {
  labels.push('documentation');
}
```

---

## 🆘 **Troubleshooting**

### **Labels Not Being Added:**
1. Check workflow ran: https://github.com/Refactron-ai/Refactron_lib/actions
2. Look for "Auto-label Bot" workflow
3. Expand logs to see why labels weren't added

### **Wrong Labels:**
1. Remove incorrect labels manually
2. Bot only adds labels, it doesn't remove them
3. Check the keyword detection rules

### **Want Different Keywords:**
1. Edit the workflow file
2. Add/remove keyword conditions
3. Commit and push
4. New issues/PRs will use updated rules

---

## 📚 **Related Documentation**

- [Issue Templates](/.github/ISSUE_TEMPLATE/) - Pre-filled issue forms
- [Pull Request Template](/.github/PULL_REQUEST_TEMPLATE.md) - PR guidelines
- [Contributing Guide](/CONTRIBUTING.md) - How to contribute

---

## 🎉 **Get Started**

Just create an issue or open a PR - the bot will handle the rest! 🏷️

**No setup required - it's already active!** ✅
