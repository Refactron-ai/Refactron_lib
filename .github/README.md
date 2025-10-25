# GitHub Bots & Automation

This directory contains configuration files for various GitHub bots and automation tools that help maintain the Refactron repository.

## 🤖 Configured Bots

### 1. **Dependabot** (`dependabot.yml`)
- **Purpose**: Automatically updates dependencies
- **Schedule**: Weekly (Mondays at 9:00 AM)
- **Updates**: GitHub Actions, Python packages, Docker
- **Features**: 
  - Auto-creates PRs for updates
  - Groups related updates
  - Ignores major version updates
  - Adds appropriate labels

### 2. **Stale Bot** (`stale.yml`)
- **Purpose**: Manages inactive issues and PRs
- **Features**:
  - Marks issues stale after 30 days
  - Closes stale issues after 7 days
  - Marks PRs stale after 14 days
  - Closes stale PRs after 3 days
  - Exempts important labels
  - Adds helpful comments

### 3. **Welcome Bot** (`welcome.yml`)
- **Purpose**: Welcomes new contributors
- **Features**:
  - Welcomes new issues
  - Welcomes new PRs
  - Welcomes new contributors
  - Provides helpful links
  - Encourages participation

### 4. **Auto-merge Bot** (`auto-merge.yml`)
- **Purpose**: Automatically merges approved PRs
- **Features**:
  - Auto-merges dependency updates
  - Auto-merges security updates
  - Requires all checks to pass
  - Requires approval
  - Adds helpful comments

## 📋 Issue Templates

### 1. **Bug Report** (`ISSUE_TEMPLATE/bug_report.md`)
- Comprehensive bug reporting template
- Includes environment details
- Includes reproduction steps
- Includes expected vs actual behavior
- Includes checklist for completeness

### 2. **Feature Request** (`ISSUE_TEMPLATE/feature_request.md`)
- Detailed feature request template
- Includes motivation and use cases
- Includes priority levels
- Includes design considerations
- Includes related issues

### 3. **Question** (`ISSUE_TEMPLATE/question.md`)
- Simple question template
- Includes what you've tried
- Includes expected answer
- Includes documentation references
- Includes checklist

## 📝 Pull Request Template

### **PR Template** (`PULL_REQUEST_TEMPLATE.md`)
- Comprehensive PR template
- Includes change type classification
- Includes testing checklist
- Includes code quality checklist
- Includes documentation checklist
- Includes security checklist
- Includes performance checklist

## 🔒 Security & Community

### 1. **Security Policy** (`SECURITY.md`)
- Supported versions
- Vulnerability reporting process
- Security response timeline
- Security best practices
- Contact information
- Security hall of fame

### 2. **Code of Conduct** (`CODE_OF_CONDUCT.md`)
- Community standards
- Expected behavior
- Unacceptable behavior
- Enforcement process
- Reporting procedures
- Contact information

### 3. **Support Guide** (`SUPPORT.md`)
- Getting help documentation
- Troubleshooting guide
- Contact information
- Response times
- Label explanations
- Quick start guide

## 🚀 How to Use

### For Contributors
1. **Issues**: Use the appropriate template when creating issues
2. **PRs**: The PR template will guide you through the process
3. **Questions**: Use the question template for help
4. **Security**: Report vulnerabilities privately

### For Maintainers
1. **Dependabot**: Reviews and merges dependency updates
2. **Stale Bot**: Manages inactive issues and PRs
3. **Welcome Bot**: Helps onboard new contributors
4. **Auto-merge**: Streamlines the review process

## 🔧 Configuration

### Dependabot
- Updates dependencies weekly
- Groups related updates
- Ignores major version updates
- Adds appropriate labels
- Assigns to maintainers

### Stale Bot
- Manages inactive issues and PRs
- Adds helpful comments
- Exempts important labels
- Maintains repository cleanliness

### Welcome Bot
- Welcomes new contributors
- Provides helpful links
- Encourages participation
- Guides users to appropriate resources

### Auto-merge Bot
- Auto-merges approved PRs
- Requires all checks to pass
- Adds helpful comments
- Streamlines the review process

## 📊 Benefits

### For the Project
- **Automated maintenance**: Dependencies stay updated
- **Clean repository**: Inactive issues are managed
- **Better onboarding**: New contributors feel welcome
- **Streamlined reviews**: Auto-merge reduces manual work
- **Security**: Vulnerabilities are patched quickly

### For Contributors
- **Clear templates**: Know what information to provide
- **Helpful guidance**: Templates guide the process
- **Faster reviews**: Auto-merge speeds up the process
- **Better support**: Clear support channels
- **Community standards**: Code of conduct ensures respect

### For Maintainers
- **Less manual work**: Bots handle routine tasks
- **Better organization**: Templates ensure consistency
- **Faster responses**: Auto-merge reduces review time
- **Security**: Dependabot patches vulnerabilities
- **Community health**: Stale bot keeps repository clean

## 🎯 Best Practices

### For Issues
- Use the appropriate template
- Provide clear descriptions
- Include reproduction steps
- Add relevant labels
- Check existing issues first

### For PRs
- Follow the PR template
- Ensure all checks pass
- Add appropriate labels
- Include tests
- Update documentation

### For Questions
- Use the question template
- Search existing issues
- Provide clear context
- Include what you've tried
- Be specific about your needs

## 🔄 Maintenance

### Regular Tasks
- Review Dependabot PRs weekly
- Check stale issues monthly
- Update bot configurations as needed
- Monitor community health
- Respond to security reports

### Monitoring
- Watch for bot failures
- Monitor community feedback
- Check security advisories
- Review dependency updates
- Ensure templates stay relevant

## 📞 Support

If you have questions about the bots or automation:
- **GitHub Issues**: Create an issue
- **Discussions**: Start a discussion
- **Email**: [Your email]
- **Community**: [Your community channels]

---

**Last updated**: [Current date]
**Version**: 1.0
