# 📦 Publishing Refactron to PyPI

This guide walks you through publishing Refactron to the Python Package Index (PyPI).

## ✅ Pre-Flight Checklist

- [x] All tests passing (90% coverage)
- [x] Package built and validated
- [x] Local installation tested
- [x] Version set to `0.1.0b1` (beta release)
- [x] README.md is comprehensive
- [x] LICENSE file included
- [x] CHANGELOG.md updated

## 🔐 Step 1: Create PyPI Account

If you don't have a PyPI account yet:

1. **Create account on PyPI**:
   - Go to https://pypi.org/account/register/
   - Fill in your details
   - Verify your email

2. **Create account on TestPyPI** (recommended for first-time publishers):
   - Go to https://test.pypi.org/account/register/
   - This is a testing environment for PyPI

3. **Generate API Token**:
   - Go to https://pypi.org/manage/account/token/
   - Create a new token with scope "Entire account (all projects)"
   - Save the token securely (it starts with `pypi-`)

## 🧪 Step 2: Test Upload (Recommended First Time)

Upload to TestPyPI first to verify everything works:

```bash
# Upload to TestPyPI
python3 -m twine upload --repository testpypi dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: <your-test-pypi-token>
```

Test installation from TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps refactron
```

## 🚀 Step 3: Upload to PyPI (Production)

Once you've verified everything works on TestPyPI:

```bash
# Upload to real PyPI
python3 -m twine upload dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: <your-pypi-token>
```

## 🎯 Alternative: Upload with Token Directly

To avoid entering credentials each time, you can use:

```bash
# For PyPI
python3 -m twine upload --repository pypi -u __token__ -p pypi-YOUR-API-TOKEN dist/*
```

## 📝 Step 4: Verify Publication

1. Check your package on PyPI:
   - https://pypi.org/project/refactron/

2. Test installation:
   ```bash
   pip install refactron
   refactron --version
   ```

3. Test the CLI:
   ```bash
   refactron analyze examples/
   ```

## 🔄 Future Updates

When you release new versions:

1. Update version in:
   - `pyproject.toml` (line 7)
   - `refactron/__init__.py` (line 11)
   - `refactron/cli.py` (line 139)

2. Update `CHANGELOG.md` with changes

3. Rebuild and upload:
   ```bash
   rm -rf dist/ build/ *.egg-info
   python3 -m build
   python3 -m twine check dist/*
   python3 -m twine upload dist/*
   ```

## 📋 Version Naming Convention

- **Alpha**: `0.1.0a1`, `0.1.0a2`, etc. (experimental)
- **Beta**: `0.1.0b1`, `0.1.0b2`, etc. (feature-complete, testing)
- **Release Candidate**: `0.1.0rc1` (almost ready)
- **Stable**: `0.1.0`, `0.2.0`, `1.0.0` (production-ready)

## 🛡️ Security Best Practices

1. **Never commit your API token** to version control
2. **Use environment variables** for tokens:
   ```bash
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-YOUR-API-TOKEN
   python3 -m twine upload dist/*
   ```
3. **Revoke old tokens** when rotating credentials

## 🐛 Troubleshooting

### "File already exists" error
You cannot re-upload the same version. Bump the version number.

### "Invalid distribution" error
Run `python3 -m twine check dist/*` to identify issues.

### "403 Forbidden" error
Check your API token permissions and ensure it hasn't expired.

### Package not found after upload
Wait a few minutes for PyPI to index your package.

## 🎉 Post-Publication

After publishing:

1. **Announce on social media** (Twitter, LinkedIn, Reddit)
2. **Update GitHub** with installation badges
3. **Write a blog post** about your library
4. **Submit to Python Weekly** newsletter
5. **Create a demo video** or tutorial

## 📊 Package Analytics

Track your package usage at:
- https://pypistats.org/packages/refactron
- https://libraries.io/pypi/refactron

## 🤝 Community

Encourage users to:
- ⭐ Star your repository
- 🐛 Report issues
- 💡 Suggest features
- 🔀 Contribute improvements

---

**Current Status**: Ready to publish `refactron 0.1.0b1` 🚀

**Package Size**: 
- Wheel: 42KB
- Source: 51KB

**Total Files**: 30+ Python modules + examples + docs

