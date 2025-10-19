# Changelog - DiscussHub

All notable changes to DiscussHub will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-10-18 🎉

### 🎊 Major Release - Complete Feature Set

First official release of DiscussHub with complete multi-channel messaging, AI auto-responses, sentiment analysis, and multi-modal capabilities.

### Added

#### 🤖 AI Features (Phase 5-6)
- **Multi-Provider AI Support**
  - Google Gemini 1.5 Pro/Flash integration
  - HuggingFace Inference API (FREE unlimited)
  - Provider selection in UI
  - Automatic provider failover
- **AI Auto-Responder** (450 LOC)
  - Context-aware responses with conversation history
  - Confidence scoring with auto-escalation
  - Custom system prompts
  - Safety settings (harassment, hate speech filtering)
  - Response history tracking with feedback
- **Sentiment Analysis** (280 LOC)
  - Real-time emotion detection with TextBlob
  - 5-level classification (very negative → very positive)
  - Automatic escalation on negative sentiment
  - Polarity and subjectivity scoring
  - Batch analysis support
  - Analytics dashboard (pivot/graph views)
- **Voice Messages** (200 LOC)
  - Speech-to-text transcription
  - Multi-language support (EN/PT-BR/ES)
  - Audio file storage and management
  - Status tracking and retry mechanism

#### 🎨 Multi-Modal AI (Phase 7)
- **Image Analysis with Gemini Vision** (280 LOC)
  - 6 analysis types: describe, OCR, object detection, product ID, sentiment, custom
  - Multi-language image descriptions
  - Auto-analyze incoming images
  - Image preview in UI
  - Custom prompts for flexible queries

#### 📱 Messaging Plugins
- **Telegram Plugin** (500 LOC)
  - Complete Bot API integration
  - Text and media messages (photo, video, audio, document)
  - Inline keyboards for interactive buttons
  - Callback query handling
  - Webhook management
- **Evolution API** (WhatsApp via Baileys) - 1,280 LOC
- **WhatsApp Cloud API** (Official Business API) - 497 LOC
- **NotificaMe** - 133 LOC

#### 🔗 Bridge Modules
- **discusshub_crm** (~450 LOC)
  - WhatsApp integration in CRM Leads/Opportunities
  - Message history tracking
  - Auto-detect phone numbers
- **discusshub_helpdesk** (~200 LOC)
  - Support ticket WhatsApp integration
  - Customer communication tracking
- **discusshub_project** (~150 LOC)
  - Project task messaging
  - Client progress updates

#### 🚀 Enterprise Features
- **Message Templates** with Jinja2 variables
  - 10 categories
  - Multi-language translation system
  - Template preview and testing
  - Attachment support
- **Bulk Messaging** (~200 LOC)
  - Mass send to multiple records
  - Rate limiting
  - Progress tracking
  - Error reporting per record
- **Analytics Dashboard** (~650 LOC)
  - SQL views for performance
  - Message metrics and trends
  - Channel activity tracking
  - Template usage statistics
- **Automated Triggers** (~550 LOC)
  - 5 trigger types (create, update, stage change, scheduled)
  - base.automation integration
  - Domain filtering
  - Template selection

#### 🎯 Routing System
- **5 Routing Strategies**
  - Round Robin: Even distribution
  - Random: Random assignment
  - Least Busy: Load-based routing
  - Skill-Based: Match agent expertise
  - Priority-Based: VIP → senior agents
- Team management
- Online status filtering
- Load tracking

#### 🧙 Setup Wizards
- **AI Setup Wizard** (4 steps)
  - Provider selection
  - API configuration
  - System instructions
  - Test before creating
- **Telegram Setup Wizard** (4 steps)
  - Bot creation guidance
  - Automatic webhook config
  - Bot verification

#### 🎨 UI & UX (100% Odoo 18)
- All views use `<list>` tags (not deprecated `<tree>`)
- Proper widgets: badge, boolean_toggle, percentage, progressbar
- Mobile-responsive kanban views
- Search views with comprehensive filters
- Help text for all actions
- Color-coded status badges

#### 📚 Documentation
- **3 Languages**: English, Portuguese (BR), Spanish (LATAM)
- **12+ Guide Documents**:
  - Main README (EN/PT/ES)
  - Bridge Modules guide (EN/PT/ES)
  - AI Features guide
  - Evolution Plugin guide
  - Plugin Development guide
  - Troubleshooting guide
  - Production Deployment guide
  - Quick Installation guide (PT-BR)
- **Technical Documentation**:
  - Implementation Roadmap
  - Phase planning documents
  - neodoo_ai integration analysis
  - Current status assessment

#### 🧪 Testing
- **127+ Tests** across 9 test files
- **3,860 LOC** of test code
- Mock patterns for external APIs
- Comprehensive coverage
- Tagged for selective running
- TransactionCase (Odoo 18 standard)

#### 🔒 Security
- **34 ACL Rules** for granular permissions
- User vs Manager role separation
- SQL constraints for data integrity
- Secure API key handling
- Content filtering (AI safety)

### Technical Specifications

- **Total LOC**: ~10,000 lines of code
- **Models**: 25+ Python models
- **Views**: 12+ XML view files
- **Plugins**: 5 messaging plugins
- **Bridge Modules**: 3 app integrations
- **AI Providers**: 2 (Gemini + HuggingFace)
- **Languages**: 3 (EN, PT-BR, ES)
- **Odoo Compliance**: 100% Odoo 18.0
- **License**: AGPL-3.0

### Dependencies

#### Python (external_dependencies)
```python
"google-generativeai",  # Gemini AI
"textblob",            # Sentiment analysis
"SpeechRecognition",   # Voice transcription
"pydub",               # Audio processing
"Pillow",              # Image processing
```

#### Odoo Modules (depends)
```python
"base",
"mail",
"base_automation",
"crm",
```

### Installation

```bash
# Quick install
pip install google-generativeai textblob SpeechRecognition pydub Pillow
# Apps → Install discuss_hub
```

### Breaking Changes

None - This is the first major release (2.0.0)

### Upgrade Notes

- Requires Odoo 18.0 (not compatible with 17.0 or earlier)
- All external Python dependencies must be installed
- Recommended: 2GB+ RAM for AI features
- Recommended: HTTPS for webhooks

---

## Version History

- **18.0.4.0.0** (2025-10-18): Multi-modal AI + Wizards + Multi-lang
- **18.0.3.0.0** (2025-10-18): Optional enhancements
- **18.0.2.0.0** (2025-10-18): Phase 6 complete (AI + Tests)
- **18.0.0.0.11** (2025-10-14): Initial implementation (Phase 1-3)

---

**Current Version**: 18.0.4.0.0
**Status**: Production-Ready ✅
**Next Release**: TBD (feature requests)

---

For detailed commit history, see: https://github.com/neoand/discuss_hub/commits/main
