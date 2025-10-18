# DiscussHub Documentation 📚

> **Complete documentation for DiscussHub - WhatsApp & Multi-Channel Integration for Odoo 18**

Welcome to the DiscussHub documentation hub! Here you'll find comprehensive guides in multiple languages.

---

## 🌍 Choose Your Language

### 🇺🇸 English

**Complete Guides:**
- **[Main Documentation](en/README.md)** - Complete overview and getting started
- **[Bridge Modules](en/Bridge%20Modules.md)** - Integrate DiscussHub with CRM, Helpdesk, Project, and custom modules
- **[Evolution Plugin](en/Evolution%20Plugin.md)** - WhatsApp integration via Evolution API
- **[Plugin Development](en/Plugin%20Development.md)** - Create custom messaging plugins

**Quick Links:**
- [Installation Guide](SETUP.md)
- [Architecture Diagrams](assets/diagrams.md)
- [Test Documentation](../tests/README.md)

---

### 🇧🇷 Português (Brasil)

**Guias Completos:**
- **[Documentação Principal](pt-br/README.md)** - Visão geral completa e início rápido
- **[Módulos Bridge](pt-br/Módulos%20Bridge.md)** - Integre DiscussHub com CRM, Helpdesk, Project e módulos customizados
- **[Plugin Evolution](pt-br/Evolution%20Plugin.md)** - Integração WhatsApp via Evolution API
- **[Desenvolvimento de Plugins](pt-br/Plugin%20Development.md)** - Crie plugins de mensageria customizados

**Links Rápidos:**
- [Guia de Instalação](SETUP.md)
- [Troubleshooting](pt-br/Troubleshooting.md) - Solução de problemas comuns
- [Diagramas de Arquitetura](assets/diagrams.md)

---

### 🇪🇸 Español (Latinoamérica)

**Guías Completas:**
- **[Documentación Principal](es/README.md)** - Visión general completa e inicio rápido
- **[Módulos Bridge](es/Módulos%20Bridge.md)** - Integración con CRM, Helpdesk, Project y módulos personalizados
- **Plugin Evolution** - Disponible en [inglés](en/Evolution%20Plugin.md)
- **Desarrollo de Plugins** - Disponible en [inglés](en/Plugin%20Development.md)

**Enlaces Rápidos:**
- [Guía de Instalación](SETUP.md)
- [Diagramas de Arquitectura](assets/diagrams.md)

---

## 📖 Documentation Structure

```
docs/
├── README.md                      # This file - Documentation hub
├── SETUP.md                       # Installation and setup guide
│
├── en/                            # 🇺🇸 English documentation
│   ├── README.md                  # Main guide
│   ├── Bridge Modules.md          # CRM/Helpdesk/Project integration guide
│   ├── Evolution Plugin.md        # WhatsApp Baileys integration
│   └── Plugin Development.md      # Create custom plugins
│
├── pt-br/                         # 🇧🇷 Brazilian Portuguese documentation
│   ├── README.md                  # Guia principal
│   ├── Módulos Bridge.md          # Guia de integração CRM/Helpdesk/Project
│   ├── Evolution Plugin.md        # Integração WhatsApp Baileys
│   ├── Plugin Development.md      # Criar plugins customizados
│   └── Troubleshooting.md         # Solução de problemas
│
├── es/                            # 🇪🇸 Spanish documentation
│   ├── README.md                  # Guía principal
│   └── Módulos Bridge.md          # Guía de integración CRM/Helpdesk/Project
│
└── assets/                        # Shared assets
    └── diagrams.md                # Architecture diagrams
```

---

## 🎯 Quick Start Guides

### For Users

1. **[Installation](SETUP.md)** - Get DiscussHub running in 5 minutes
2. **[Main Guide (EN)](en/README.md)** | **[Guia Principal (PT)](pt-br/README.md)** | **[Guía Principal (ES)](es/README.md)** - Learn the basics
3. **[Evolution Plugin](en/Evolution%20Plugin.md)** - Connect WhatsApp

### For Developers

1. **[Bridge Modules (EN)](en/Bridge%20Modules.md)** | **[Módulos Bridge (PT)](pt-br/Módulos%20Bridge.md)** - Integrate with Odoo apps
2. **[Plugin Development](en/Plugin%20Development.md)** - Create new messaging providers
3. **[Test Documentation](../tests/README.md)** - Testing guidelines

### For DevOps

1. **[Docker Setup](../compose.yaml)** - Production deployment
2. **[Development Setup](../compose-dev.yaml)** - Local development environment
3. **[Troubleshooting (PT)](pt-br/Troubleshooting.md)** - Common issues

---

## 📚 Documentation Topics

### Core Concepts

- **Connectors** - Manage messaging service connections
- **Plugins** - Extensible architecture for different providers
- **Channels** - Integration with Odoo Discuss
- **Webhooks** - Real-time message processing

### Integration

- **DiscussHub Mixin** - Add messaging to any Odoo model
- **Bridge Modules** - Pre-built integrations for CRM, Helpdesk, Project
- **Custom Bridges** - Create your own integrations

### Enterprise Features

- **Message Templates** - Reusable Jinja2-based templates
- **Bulk Messaging** - Send campaigns with rate limiting
- **Automated Triggers** - Event-based message automation
- **Analytics** - Messaging metrics and reports

### Advanced

- **Multi-Language** - Template translation support
- **Routing** - Distribute conversations to team members
- **Bot Management** - Automated responses
- **N8N Integration** - Workflow automation

---

## 🤝 Contributing to Documentation

We welcome documentation improvements!

### How to Contribute

1. **Fix typos or errors**: Submit a PR directly
2. **Add translations**: Create new language directories following the structure
3. **Add examples**: Practical code examples are always welcome
4. **Improve clarity**: Rewrite confusing sections

### Translation Guidelines

- Keep the same structure as English docs
- Translate technical terms consistently
- Update the language table in this README
- Add language flag emoji to titles

### Supported Languages

- ✅ English (Complete - 4 guides)
- ✅ Português Brasileiro (Complete - 5 guides)
- ✅ Español Latinoamericano (Complete - 2 guides)
- 📋 Français (Planned)
- 📋 Deutsch (Planned)
- 📋 中文 Chinese (Planned)

---

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/neoand/discuss_hub/issues)
- **GitHub Discussions**: [Ask questions or share ideas](https://github.com/neoand/discuss_hub/discussions)
- **Documentation Issues**: Tag with `documentation` label

---

## 📄 License

Documentation is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

Code examples are licensed under [AGPL-3.0](../LICENSE)

---

**Last Updated**: October 17, 2025
**Version**: 1.0.0
**Compatibility**: Odoo 18.0+, DiscussHub 18.0.1.0.0+

---

**Made with ❤️ by the DiscussHub Team**
