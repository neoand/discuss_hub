# Contributing to DiscussHub 🤝

> **Help us build the best multi-channel messaging integration for Odoo!**

Thank you for your interest in contributing to DiscussHub! This document provides guidelines for contributing to the project.

---

## 🌍 Language Contributions

We welcome documentation translations! Currently supported:

- ✅ English (Primary)
- ✅ Português Brasileiro (Complete)
- ✅ Español Latinoamericano (Complete)
- 📋 Français (Planned)
- 📋 Deutsch (Planned)
- 📋 中文 Chinese (Planned)

### How to Contribute Translations

1. **Choose a language** not yet fully translated
2. **Follow the structure** in `community_addons/discuss_hub/docs/en/`
3. **Translate guides** maintaining technical accuracy
4. **Update** `docs/README.md` with new language links
5. **Submit PR** with translation

---

## 🚀 Quick Contributing Guide

### For Developers

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/discuss_hub.git
   cd discuss_hub
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes**
   - Follow Odoo coding standards
   - Add tests for new features
   - Update documentation

4. **Run tests**
   ```bash
   docker compose -f compose-dev.yaml exec odoo odoo \
     -c /etc/odoo/odoo.conf --test-enable \
     --stop-after-init -u discuss_hub
   ```

5. **Submit Pull Request**
   - Clear description of changes
   - Link to related issues
   - Screenshots if UI changes

---

## 📋 Development Standards

### Code Quality

- ✅ **Odoo 18.0+ compatible**
- ✅ **Python 3.10+ syntax**
- ✅ **PEP 8 compliant** (use `ruff` linter)
- ✅ **Type hints** where applicable
- ✅ **Comprehensive docstrings**
- ✅ **Error handling** with proper logging

### Testing Requirements

- ✅ **Unit tests** for all new features
- ✅ **Integration tests** for plugins
- ✅ **Test coverage** > 70%
- ✅ **Mock external services** properly
- ✅ **Test documentation** in `tests/README.md`

### Documentation Standards

- ✅ **Update relevant guides** when adding features
- ✅ **Code examples** for all public APIs
- ✅ **Inline comments** for complex logic
- ✅ **Changelog entry** for user-facing changes
- ✅ **Screenshots** for UI changes

---

## 🧪 Testing Your Contributions

### Run All Tests

```bash
# Full test suite
docker compose -f compose-dev.yaml exec odoo odoo \
  -c /etc/odoo/odoo.conf --test-enable \
  --stop-after-init -u discuss_hub

# Specific test file
docker compose -f compose-dev.yaml exec odoo odoo \
  -c /etc/odoo/odoo.conf --test-enable \
  --stop-after-init -u discuss_hub \
  --test-tags /discuss_hub:TestEvolutionPlugin
```

### Pre-commit Checks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Quality Checks

```bash
# Python linting
ruff check community_addons/discuss_hub/

# Python formatting
ruff format community_addons/discuss_hub/

# JavaScript linting
npm run lint
```

---

## 🐛 Reporting Issues

When reporting bugs or requesting features, please use our templates:

### Bug Report Template

```markdown
## Bug Description
Clear and concise description of the bug

## To Reproduce
1. Go to '...'
2. Click on '....'
3. See error

## Expected Behavior
What should happen instead

## Environment
- Odoo version: 18.0
- DiscussHub version: X.X.X
- Plugin: Evolution / WhatsApp Cloud / etc
- Browser (if applicable): Chrome 120

## Screenshots
If applicable, add screenshots

## Additional Context
Logs, error messages, etc.
```

### Feature Request Template

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed? Who will use it?

## Proposed Solution
How would you like this to work?

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Mockups, examples from other apps, etc.
```

---

## 🔌 Creating New Plugins

Want to add support for a new messaging platform?

### Plugin Structure

```python
# community_addons/discuss_hub/discuss_hub/models/plugins/your_plugin.py

from .base import DiscussHubPluginBase

class YourPlugin(DiscussHubPluginBase):
    """Plugin for Your Messaging Platform."""

    _name = 'your_platform'
    _description = 'Your Platform Integration'

    def send_message(self, channel, body, **kwargs):
        """Send message via Your Platform API."""
        # Implementation
        pass

    def process_incoming_message(self, payload):
        """Process incoming webhook from Your Platform."""
        # Implementation
        pass
```

### Required Methods

- `send_message()` - Send text message
- `send_media()` - Send media files
- `process_incoming_message()` - Handle webhook
- `get_qr_code()` - Get QR for authentication (if applicable)

### Testing Your Plugin

```python
# tests/test_your_plugin.py

class TestYourPlugin(TransactionCase):

    def setUp(self):
        super().setUp()
        self.plugin = self.env['discuss_hub.connector'].create({
            'name': 'Test Your Platform',
            'type': 'your_platform',
            # ...
        })

    def test_send_message(self):
        # Test implementation
        pass
```

---

## 🌉 Creating Bridge Modules

Want to integrate DiscussHub with another Odoo app?

### Quick Start

See our comprehensive guides:
- [English Guide](community_addons/discuss_hub/docs/en/Bridge%20Modules.md#creating-your-own-bridge)
- [Guía en Español](community_addons/discuss_hub/docs/es/Módulos%20Bridge.md#crear-tu-propio-bridge)
- [Guia em Português](community_addons/discuss_hub/docs/pt-br/Módulos%20Bridge.md#como-criar-seu-próprio-bridge)

### Minimum Requirements

1. **Inherit `discusshub.mixin`**
2. **Add buttons to form view**
3. **Test integration**
4. **Document usage**

---

## 📚 Documentation Contributions

### Documentation Structure

```
docs/
├── en/          # English (primary)
├── pt-br/       # Portuguese
├── es/          # Spanish
└── assets/      # Shared images
```

### Adding a New Guide

1. **Create file** in appropriate language folder
2. **Follow existing structure** (see other guides)
3. **Add links** from main README
4. **Update docs/README.md**
5. **Translate to other languages** (or mark as "Translation needed")

### Writing Style

- ✅ **Clear and concise**
- ✅ **Use examples liberally**
- ✅ **Include code snippets**
- ✅ **Add screenshots** when helpful
- ✅ **Link to related docs**

---

## 🏷️ Versioning & Releases

We follow [Semantic Versioning](https://semver.org/):

- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backwards compatible
- **Patch** (0.0.X): Bug fixes

### Release Process

1. Update version in `__manifest__.py`
2. Update `CHANGELOG.md`
3. Tag release: `git tag -a vX.Y.Z -m "Version X.Y.Z"`
4. Push tags: `git push origin vX.Y.Z`
5. Create GitHub release with notes

---

## 🤝 Community Guidelines

### Code of Conduct

- **Be respectful** and inclusive
- **Help newcomers** learn
- **Give constructive feedback**
- **Celebrate contributions** of all sizes

### Pull Request Etiquette

- **One feature per PR**
- **Clear commit messages**
- **Link related issues**
- **Respond to review comments**
- **Keep PRs small** and focused

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** by maintainer
3. **Test in dev environment**
4. **Merge** when approved

---

## 🛠️ Development Setup

### Using Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/neoand/discuss_hub.git
cd discuss_hub

# Start development environment
docker compose -f compose-dev.yaml up -d

# Access Odoo
# URL: http://localhost:8069
# User: admin / Password: admin

# View logs
docker compose -f compose-dev.yaml logs -f odoo

# Run tests
docker compose -f compose-dev.yaml exec odoo odoo \
  -c /etc/odoo/odoo.conf --test-enable \
  --stop-after-init -u discuss_hub
```

### Local Setup (Alternative)

```bash
# Install dependencies
pip install -r requirements.txt

# Configure database
createdb discuss_hub_dev

# Run Odoo
./odoo-bin -c odoo.conf -d discuss_hub_dev --dev=all
```

---

## 📞 Getting Help

- **GitHub Issues**: [Bug reports & features](https://github.com/neoand/discuss_hub/issues)
- **GitHub Discussions**: [Questions & ideas](https://github.com/neoand/discuss_hub/discussions)
- **Documentation**: [Complete guides](community_addons/discuss_hub/docs)

---

## 📜 License

By contributing to DiscussHub, you agree that your contributions will be licensed under the **AGPL-3.0 License**.

---

**Thank you for contributing to DiscussHub!** 🎉

Together we're making Odoo messaging integration better for everyone.

---

**Made with ❤️ by the DiscussHub Community**
