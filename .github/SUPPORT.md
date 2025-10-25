# Support

## 🆘 Getting Help

### 📚 Documentation
- **README**: [Main documentation](https://github.com/Refactron-ai/Refactron_lib/blob/main/README.md)
- **Getting Started**: [Developer guide](https://github.com/Refactron-ai/Refactron_lib/blob/main/GETTING_STARTED_DEV.md)
- **Architecture**: [Technical details](https://github.com/Refactron-ai/Refactron_lib/blob/main/ARCHITECTURE.md)
- **Case Study**: [Real-world examples](https://github.com/Refactron-ai/Refactron_lib/blob/main/CASE_STUDY.md)

### 🐛 Bug Reports
- **Template**: Use the [Bug Report template](https://github.com/Refactron-ai/Refactron_lib/issues/new?template=bug_report.md)
- **Search**: Check [existing issues](https://github.com/Refactron-ai/Refactron_lib/issues) first
- **Labels**: Look for `bug` and `help-wanted` labels

### ✨ Feature Requests
- **Template**: Use the [Feature Request template](https://github.com/Refactron-ai/Refactron_lib/issues/new?template=feature_request.md)
- **Discussion**: Start a [discussion](https://github.com/Refactron-ai/Refactron_lib/discussions) for complex features
- **Labels**: Look for `enhancement` and `good-first-issue` labels

### ❓ Questions
- **Template**: Use the [Question template](https://github.com/Refactron-ai/Refactron_lib/issues/new?template=question.md)
- **Discussions**: Use [GitHub Discussions](https://github.com/Refactron-ai/Refactron_lib/discussions)
- **Labels**: Look for `question` and `help-wanted` labels

## 🚀 Quick Start

### Installation
```bash
pip install refactron
```

### Basic Usage
```bash
# Analyze your code
refactron analyze your_project/

# Get refactoring suggestions
refactron refactor your_file.py --preview
```

### Python API
```python
from refactron import Refactron
from refactron.core.config import RefactronConfig

config = RefactronConfig.default()
refactron = Refactron(config)
result = refactron.analyze("your_project/")
```

## 🔧 Troubleshooting

### Common Issues

#### 1. **Installation Problems**
```bash
# Update pip
pip install --upgrade pip

# Install with specific Python version
python3.8 -m pip install refactron
```

#### 2. **Import Errors**
```bash
# Check Python version
python --version

# Verify installation
pip show refactron
```

#### 3. **Permission Errors**
```bash
# Use --user flag
pip install --user refactron

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
pip install refactron
```

#### 4. **Analysis Errors**
```bash
# Check file permissions
ls -la your_file.py

# Use verbose mode
refactron analyze your_file.py --verbose
```

## 📞 Contact

### 🐛 Bug Reports
- **GitHub Issues**: [Create an issue](https://github.com/Refactron-ai/Refactron_lib/issues/new?template=bug_report.md)
- **Email**: [Your email]
- **Discord/Slack**: [Your community channels]

### ✨ Feature Requests
- **GitHub Issues**: [Create an issue](https://github.com/Refactron-ai/Refactron_lib/issues/new?template=feature_request.md)
- **Discussions**: [Start a discussion](https://github.com/Refactron-ai/Refactron_lib/discussions)
- **Email**: [Your email]

### ❓ General Questions
- **GitHub Discussions**: [Ask a question](https://github.com/Refactron-ai/Refactron_lib/discussions)
- **GitHub Issues**: [Create an issue](https://github.com/Refactron-ai/Refactron_lib/issues/new?template=question.md)
- **Email**: [Your email]

### 🤝 Contributing
- **Contributing Guide**: [CONTRIBUTING.md](https://github.com/Refactron-ai/Refactron_lib/blob/main/CONTRIBUTING.md)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](https://github.com/Refactron-ai/Refactron_lib/blob/main/CODE_OF_CONDUCT.md)
- **Security**: [SECURITY.md](https://github.com/Refactron-ai/Refactron_lib/blob/main/SECURITY.md)

## 🏷️ Labels

### Issue Labels
- `bug` - Bug reports
- `enhancement` - Feature requests
- `question` - Questions
- `documentation` - Documentation updates
- `good-first-issue` - Good for new contributors
- `help-wanted` - Help needed
- `priority-high` - High priority
- `priority-medium` - Medium priority
- `priority-low` - Low priority

### PR Labels
- `dependencies` - Dependency updates
- `security` - Security updates
- `performance` - Performance improvements
- `refactoring` - Code refactoring
- `testing` - Test updates
- `breaking-change` - Breaking changes

## 📋 Response Times

- **Critical Issues**: Within 24 hours
- **Bug Reports**: Within 72 hours
- **Feature Requests**: Within 1 week
- **Questions**: Within 3 days
- **General Support**: Within 1 week

## 🙏 Acknowledgments

We thank our community for:
- Reporting bugs and issues
- Suggesting new features
- Contributing code and documentation
- Helping other users
- Making Refactron better

---

**Last updated**: [Current date]
**Version**: 1.0
