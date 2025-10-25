# Refactron GitHub Pages

This directory contains the GitHub Pages site for Refactron.

## 🌐 Live Site

Visit: **https://refactron-ai.github.io/Refactron_lib/**

## 📁 Structure

- `index.html` - Main landing page with modern, animated design
- `_config.yml` - GitHub Pages configuration
- `.nojekyll` - Disables Jekyll processing (we use plain HTML)

## 🎨 Features

The landing page includes:
- ✨ Animated gradient background
- 📱 Fully responsive design
- 🚀 Quick start guide with code examples
- 📊 Feature highlights and statistics
- 🔗 Links to PyPI, GitHub, and documentation
- 🎯 Call-to-action buttons
- 🌙 Modern dark theme

## 🛠️ Local Development

To preview locally:

```bash
# Option 1: Python HTTP server
cd docs
python -m http.server 8000

# Option 2: Using any static server
npx serve docs
```

Then visit: http://localhost:8000

## 📝 Customization

To customize the site:
1. Edit `index.html` for content and styling
2. Modify colors in CSS variables (`:root` section)
3. Update links and badges
4. Add custom domain in `CNAME` file (if needed)

## 🚀 Deployment

GitHub Pages automatically deploys from the `docs/` directory on the `main` branch.

Any push to `main` with changes in `docs/` will trigger a new deployment.

