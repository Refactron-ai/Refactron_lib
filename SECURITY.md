# Security Policy

## Supported Versions

We actively support the following versions of Refactron with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Refactron seriously. If you discover a security vulnerability, please follow these steps:

### 1. **Do Not** Open a Public Issue

Please do not open a public GitHub issue for security vulnerabilities. This helps prevent exploitation before a fix is available.

### 2. Report Privately

Report security vulnerabilities by emailing: **security@refactron.us.kg**

Include the following information:
- Description of the vulnerability
- Steps to reproduce the issue
- Affected versions
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **Initial Response**: Within 48 hours of submission
- **Status Update**: Within 7 days with assessment
- **Fix Timeline**: Critical issues within 14 days, others within 30 days

### 4. Disclosure Policy

We follow responsible disclosure:
- We will work with you to understand and address the issue
- We will credit you in the security advisory (unless you prefer to remain anonymous)
- We will publicly disclose the vulnerability only after a fix is released
- We typically wait 90 days before full disclosure

## Security Best Practices

When using Refactron, follow these security best practices:

### 1. **Code Execution**
- Refactron analyzes code using AST parsing and **never executes** analyzed code
- It's safe to analyze untrusted code

### 2. **File Permissions**
- Ensure Refactron has appropriate file permissions
- Review suggested refactorings before applying them
- Always backup your code before applying automated refactorings

### 3. **Dependencies**
- Keep Refactron and its dependencies up to date
- We use Dependabot to monitor and update dependencies
- Review dependency updates in our release notes

### 4. **Configuration Files**
- Protect your `.refactron.yaml` configuration files
- Don't commit sensitive information to configuration files
- Use environment variables for sensitive settings

### 5. **CI/CD Integration**
- When using Refactron in CI/CD pipelines:
  - Use read-only mode for analysis
  - Review changes before merging
  - Limit file system access appropriately

## Known Security Considerations

### Static Analysis Only
Refactron performs static analysis and does not:
- Execute analyzed code
- Make network requests (except for updates)
- Access system resources beyond the specified project directory

### Refactoring Safety
- All refactorings are previewed before application
- Risk scores are provided for each refactoring (0.0 = safe, 1.0 = high risk)
- You must explicitly approve changes before they are applied

## Security Scanning

We use multiple tools to ensure code security:

- **Bandit**: Python security linting
- **Safety**: Dependency vulnerability scanning
- **CodeQL**: Advanced semantic code analysis
- **Dependabot**: Automated dependency updates

## Third-Party Dependencies

We carefully vet all dependencies:

- **libcst**: Concrete syntax tree manipulation (maintained by Instagram/Meta)
- **astroid**: AST analysis (maintained by PyCQA)
- **radon**: Code metrics (well-established tool)
- **click**: CLI framework (maintained by Pallets)
- **rich**: Terminal formatting (actively maintained)
- **pyyaml**: YAML parsing (standard library quality)

All dependencies are regularly updated and monitored for vulnerabilities.

## Security Audit History

| Date       | Type           | Findings | Status   |
|------------|----------------|----------|----------|
| 2024-10-31 | Code Review    | 0        | ✅ Clean |
| 2024-10-31 | Dependency     | 0        | ✅ Clean |

## Hall of Fame

We recognize security researchers who help keep Refactron secure:

*No security issues reported yet. Be the first!*

## Questions?

If you have security questions or concerns that are not vulnerabilities, please:
- Open a discussion on GitHub
- Email: support@refactron.us.kg
- Review our [Contributing Guidelines](CONTRIBUTING.md)

---

**Thank you for helping keep Refactron and its users safe!** 🔒
