# Phase 6: Production Readiness - TODO List ✅

> **CRITICAL: Follow ONLY Odoo 18.0 standards - NO deprecated patterns!**

**Created**: October 18, 2025
**Target Version**: 18.0.2.0.0
**Odoo Version**: 18.0 (NO backwards compatibility with 17, 16, 15!)

---

## ⚠️ ODOO 18 STANDARDS - MANDATORY

### View Standards (DO NOT DEVIATE!)

```xml
<!-- ✅ CORRECT - Odoo 18 -->
<list>...</list>                          <!-- List views use <list> tag -->
view_mode="list,form"                     <!-- Use "list" not "tree" -->
view_mode="kanban,list,form"              <!-- Kanban first, then list -->

<!-- ❌ WRONG - Old Odoo versions -->
<tree>...</tree>                          <!-- DEPRECATED in Odoo 18 -->
view_mode="tree,form"                     <!-- WRONG - use "list" -->
```

### Chatter Standards (Odoo 18)

```xml
<!-- ✅ CORRECT - Odoo 18 mail.thread -->
<div class="oe_chatter">
    <field name="message_follower_ids"/>
    <field name="message_ids"/>
</div>

<!-- Model must inherit -->
_inherit = ['mail.thread', 'mail.activity.mixin']
```

### Widget Standards (Odoo 18)

```xml
<!-- ✅ CORRECT -->
<field name="state" widget="badge"/>
<field name="priority" widget="priority"/>
<field name="color" widget="color_picker"/>

<!-- ❌ WRONG - Old widgets -->
widget="statusbar"  <!-- Use widget="badge" for Odoo 18 -->
```

### Python Dependencies

```python
# ✅ CORRECT - Odoo 18
from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError, ValidationError

# Use Command for relational fields
partner_ids = [(Command.link(partner.id))]
partner_ids = [(Command.set([1, 2, 3]))]

# ❌ WRONG - Old syntax
partner_ids = [(6, 0, [1, 2, 3])]  <!-- Still works but deprecated -->
```

---

## 📋 PHASE 6A: CRITICAL INFRASTRUCTURE (Week 1)

### Priority: 🔴 MAXIMUM - MUST BE DONE FIRST

---

### Task 1: Create AI Responder Views ✅

**File**: `community_addons/discuss_hub/discuss_hub/views/ai_responder_views.xml`

**Requirements**:
- [x] Review Odoo 18 view standards
- [ ] Create list view (use `<list>` tag, NOT `<tree>`)
- [ ] Create form view with proper notebook structure
- [ ] Create kanban view for mobile
- [ ] Add menu item under "Configuration"
- [ ] Add action with `view_mode="kanban,list,form"` (NOT "tree")
- [ ] Use proper widgets: badge, priority, etc
- [ ] NO deprecated elements

**XML Structure** (Odoo 18 Standards):
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- List View - USE <list> NOT <tree> -->
    <record id="view_ai_responder_list" model="ir.ui.view">
        <field name="name">discuss_hub.ai_responder.view.list</field>
        <field name="model">discuss_hub.ai_responder</field>
        <field name="arch" type="xml">
            <list string="AI Responders">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="model"/>
                <field name="active" widget="boolean_toggle"/>
                <field name="confidence_threshold" widget="percentage"/>
                <field name="response_count"/>
                <field name="success_count"/>
            </list>
        </field>
    </record>

    <!-- Form View -->
    <record id="view_ai_responder_form" model="ir.ui.view">
        <field name="name">discuss_hub.ai_responder.view.form</field>
        <field name="model">discuss_hub.ai_responder</field>
        <field name="arch" type="xml">
            <form string="AI Responder">
                <header>
                    <button name="action_test_response" string="Test AI" type="object" class="btn-primary"/>
                </header>
                <sheet>
                    <widget name="web_ribbon" title="Archived" bg_color="text-bg-danger"
                            invisible="active"/>
                    <div class="oe_title">
                        <h1>
                            <field name="name" placeholder="e.g., Customer Service AI"/>
                        </h1>
                    </div>
                    <group>
                        <group>
                            <field name="active" invisible="1"/>
                            <field name="sequence"/>
                            <field name="connector_ids" widget="many2many_tags"/>
                        </group>
                        <group>
                            <field name="model" readonly="1"/>
                            <field name="confidence_threshold" widget="percentage"/>
                            <field name="temperature"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Configuration" name="config">
                            <group>
                                <group string="Google Gemini">
                                    <field name="api_key" password="True"/>
                                    <field name="max_tokens"/>
                                </group>
                                <group string="Safety Settings">
                                    <field name="safety_harassment"/>
                                    <field name="safety_hate_speech"/>
                                </group>
                            </group>
                            <group string="System Prompt">
                                <field name="system_prompt" widget="text" nolabel="1"/>
                            </group>
                        </page>
                        <page string="Context" name="context">
                            <group>
                                <field name="use_conversation_history"/>
                                <field name="history_messages_count"
                                       invisible="not use_conversation_history"/>
                            </group>
                        </page>
                        <page string="Statistics" name="stats">
                            <group>
                                <group>
                                    <field name="response_count"/>
                                    <field name="success_count"/>
                                    <field name="escalation_count"/>
                                </group>
                                <group>
                                    <field name="average_confidence" widget="percentage"/>
                                </group>
                            </group>
                            <button name="action_view_history" string="View Response History"
                                    type="object" class="btn-link"/>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>

    <!-- Kanban View -->
    <record id="view_ai_responder_kanban" model="ir.ui.view">
        <field name="name">discuss_hub.ai_responder.view.kanban</field>
        <field name="model">discuss_hub.ai_responder</field>
        <field name="arch" type="xml">
            <kanban class="o_kanban_mobile">
                <field name="name"/>
                <field name="model"/>
                <field name="active"/>
                <field name="response_count"/>
                <templates>
                    <t t-name="card">
                        <div class="oe_kanban_global_click">
                            <div class="row">
                                <div class="col-12">
                                    <strong><field name="name"/></strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-6">
                                    Model: <field name="model"/>
                                </div>
                                <div class="col-6">
                                    Responses: <field name="response_count"/>
                                </div>
                            </div>
                        </div>
                    </t>
                </templates>
            </kanban>
        </field>
    </record>

    <!-- Action - USE "list" NOT "tree" -->
    <record id="action_ai_responder" model="ir.actions.act_window">
        <field name="name">AI Responders</field>
        <field name="res_model">discuss_hub.ai_responder</field>
        <field name="view_mode">kanban,list,form</field>  <!-- NO "tree"! -->
    </record>

    <!-- Menu Item -->
    <menuitem id="menu_ai_responder"
              name="AI Responders"
              parent="menu_discuss_hub_config"
              action="action_ai_responder"
              sequence="50"/>
</odoo>
```

**Estimated Time**: 6 hours

---

### Task 2: Create AI Response History Views ✅

**File**: `community_addons/discuss_hub/discuss_hub/views/ai_response_history_views.xml`

**Requirements**:
- [ ] List view with `<list>` tag
- [ ] Form view for response details
- [ ] Search view with filters
- [ ] Action with `view_mode="list,form"` (NO "tree")
- [ ] No menu (accessed via button from AI Responder)

**Estimated Time**: 3 hours

---

### Task 3: Update Telegram Plugin Integration ✅

**File**: `community_addons/discuss_hub/discuss_hub/models/models.py`

**Requirements**:
- [ ] Add 'telegram' to connector type selection
- [ ] Add ondelete={'telegram': 'cascade'}
- [ ] Ensure plugin loads correctly

```python
# models/models.py - Update DiscussHubConnector

type = fields.Selection(
    [
        ("evolution", "Evolution API"),
        ("example", "Example Plugin"),
        ("notificame", "NotificaMe"),
        ("whatsapp_cloud", "WhatsApp Cloud API"),
        ("telegram", "Telegram Bot API"),  # ADD THIS
    ],
    string="Type",
    required=True,
    default="evolution",
    help="Select the messaging platform plugin",
    ondelete={
        'telegram': 'cascade',  # ADD THIS
    }
)
```

**Estimated Time**: 1 hour

---

### Task 4: Update Security Rules ✅

**File**: `community_addons/discuss_hub/discuss_hub/security/ir.model.access.csv`

**Requirements**:
- [ ] Add ACL for discuss_hub.ai_responder (user read, manager full)
- [ ] Add ACL for discuss_hub.ai_response_history (user read, manager full)
- [ ] Follow exact CSV format of existing entries
- [ ] Test with restricted user

```csv
# ADD THESE LINES (follow existing format):
access_discuss_hub_ai_responder_user,access_discuss_hub_ai_responder_user,model_discuss_hub_ai_responder,discuss_hub.group_discuss_hub_user,1,0,0,0
access_discuss_hub_ai_responder_manager,access_discuss_hub_ai_responder_manager,model_discuss_hub_ai_responder,discuss_hub.group_discuss_hub_manager,1,1,1,1
access_discuss_hub_ai_response_history_user,access_discuss_hub_ai_response_history_user,model_discuss_hub_ai_response_history,discuss_hub.group_discuss_hub_user,1,0,0,0
access_discuss_hub_ai_response_history_manager,access_discuss_hub_ai_response_history_manager,model_discuss_hub_ai_response_history,discuss_hub.group_discuss_hub_manager,1,1,1,1
```

**Estimated Time**: 2 hours

---

### Task 5: Update __manifest__.py ✅

**File**: `community_addons/discuss_hub/discuss_hub/__manifest__.py`

**Requirements**:
- [ ] Add new view files to 'data' list
- [ ] Add external_dependencies for google-generativeai
- [ ] Update version to 18.0.2.0.0
- [ ] Follow existing format EXACTLY

```python
{
    "name": "discuss_hub",
    "version": "18.0.2.0.0",  # UPDATE VERSION
    "depends": ["base", "mail", "base_automation", "crm"],
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/templates.xml",
        "views/res_partner_view.xml",
        "views/message_template_views.xml",
        "views/bulk_send_wizard_views.xml",
        "views/analytics_views.xml",
        "views/automated_trigger_views.xml",
        # Phase 5: AI Features
        "views/ai_responder_views.xml",  # ADD THIS
        "views/ai_response_history_views.xml",  # ADD THIS
        "datas/base_automation.xml",
        "wizard/mail_discuss_channel_forward.xml",
        "wizard/mail_discuss_channel_archive.xml",
    ],
    "external_dependencies": {  # ADD THIS SECTION
        "python": [
            "google-generativeai",
            "textblob",
        ],
    },
    "assets": {
        "web.assets_backend": [
            "discuss_hub/static/src/js/discuss_channel_actions.esm.js",
        ],
    },
    "demo": [
        "demo/demo.xml",
        "data/message_templates.xml",
    ],
}
```

**Estimated Time**: 1 hour

---

### Task 6: Fix Existing view_mode References ✅

**Files to Fix**:
- `views/message_template_views.xml` (line 177)
- `views/automated_trigger_views.xml` (line 231)
- `models/message_template.py` (line 396)
- `models/ai_responder.py` (line 488)
- `models/analytics.py` (lines 474, 487)

**Change ALL occurrences**:
```python
# FIND:
'view_mode': 'tree,form'

# REPLACE WITH:
'view_mode': 'list,form'
```

**Estimated Time**: 1 hour

---

## 📋 PHASE 6B: MISSING IMPLEMENTATIONS (Week 2)

### Task 7: Implement Sentiment Analyzer ✅

**File**: `community_addons/discuss_hub/discuss_hub/models/sentiment_analyzer.py`

**Requirements**:
- [ ] Create model `discuss_hub.sentiment_analyzer`
- [ ] Use TextBlob for analysis
- [ ] Store polarity, subjectivity, sentiment
- [ ] Automatic escalation logic
- [ ] Link to mail.message
- [ ] NO deprecated patterns

```python
"""Sentiment Analysis for Messages - Odoo 18"""

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

class SentimentAnalyzer(models.Model):
    _name = 'discuss_hub.sentiment_analyzer'
    _description = 'Message Sentiment Analysis'
    _order = 'create_date desc'

    message_id = fields.Many2one('mail.message', required=True, ondelete='cascade')
    channel_id = fields.Many2one('discuss.channel', related='message_id.res_id')

    sentiment = fields.Selection([
        ('very_negative', 'Very Negative'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('positive', 'Positive'),
        ('very_positive', 'Very Positive'),
    ], compute='_compute_sentiment', store=True)

    polarity = fields.Float(string='Polarity', help='Range: -1 (negative) to +1 (positive)')
    subjectivity = fields.Float(string='Subjectivity', help='Range: 0 (objective) to 1 (subjective)')

    escalated = fields.Boolean(default=False)
    escalation_reason = fields.Text()

    @api.depends('polarity')
    def _compute_sentiment(self):
        for record in self:
            if record.polarity <= -0.6:
                record.sentiment = 'very_negative'
            elif record.polarity <= -0.2:
                record.sentiment = 'negative'
            elif record.polarity <= 0.2:
                record.sentiment = 'neutral'
            elif record.polarity <= 0.6:
                record.sentiment = 'positive'
            else:
                record.sentiment = 'very_positive'

    @api.model
    def analyze_message(self, message):
        """Analyze sentiment of message"""
        if not TEXTBLOB_AVAILABLE:
            raise UserError(_('TextBlob not installed'))

        blob = TextBlob(message.body)

        analyzer = self.create({
            'message_id': message.id,
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity,
        })

        # Auto-escalate if very negative
        if analyzer.sentiment == 'very_negative':
            analyzer.trigger_escalation()

        return analyzer

    def trigger_escalation(self):
        """Escalate negative sentiment to supervisor"""
        self.ensure_one()
        # Implementation here
        self.escalated = True
```

**Estimated Time**: 8 hours

---

### Task 8: Create Sentiment Views ✅

**File**: `community_addons/discuss_hub/discuss_hub/views/sentiment_analyzer_views.xml`

**Requirements**:
- [ ] List view with `<list>` (NO `<tree>`)
- [ ] Form view
- [ ] Graph view for analytics
- [ ] Action with correct view_mode
- [ ] Menu under "Analytics"

**Estimated Time**: 4 hours

---

### Task 9: Update models/__init__.py ✅

**File**: `community_addons/discuss_hub/discuss_hub/models/__init__.py`

**Current**:
```python
from . import ai_responder  # Phase 5: AI-powered auto-responses with Google Gemini
```

**Add**:
```python
from . import ai_responder  # Phase 5: AI with Google Gemini
from . import sentiment_analyzer  # Phase 5: Sentiment analysis
# from . import voice_message  # Phase 5: Voice transcription (future)
# from . import message_template_translation  # Phase 4: Multi-lang (future)
```

**Estimated Time**: 10 minutes

---

### Task 10: Update plugins/__init__.py ✅

**File**: `community_addons/discuss_hub/discuss_hub/models/plugins/__init__.py`

**Check if telegram is imported**:
```python
from . import base
from . import evolution
from . import example
from . import notificame
from . import whatsapp_cloud
from . import telegram  # ADD IF MISSING
```

**Estimated Time**: 10 minutes

---

## 📋 PHASE 6C: TESTING & QA (Week 3)

### Task 11: Create AI Responder Tests ✅

**File**: `community_addons/discuss_hub/discuss_hub/tests/test_ai_responder.py`

**Requirements**:
- [ ] Use TransactionCase (Odoo 18 standard)
- [ ] Mock Google AI API
- [ ] Test generate_response()
- [ ] Test confidence calculation
- [ ] Test escalation logic
- [ ] Test conversation history
- [ ] NO deprecated test patterns

```python
"""Tests for AI Responder - Odoo 18"""

from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestAIResponder(TransactionCase):
    """Test Google Gemini AI Responder"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ai_responder = cls.env['discuss_hub.ai_responder'].create({
            'name': 'Test AI',
            'api_key': 'test_key',
            'model': 'gemini-1.5-flash',
            'confidence_threshold': 0.80,
        })

    @patch('google.generativeai.GenerativeModel')
    def test_generate_response(self, mock_model):
        """Test AI response generation"""
        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = "Hello! How can I help you?"
        mock_model.return_value.start_chat.return_value.send_message.return_value = mock_response

        result = self.ai_responder.generate_response("Hi")

        self.assertTrue(result['text'])
        self.assertIn('confidence', result)
        self.assertIn('should_auto_respond', result)

    def test_confidence_threshold(self):
        """Test auto-respond decision"""
        self.ai_responder.confidence_threshold = 0.80

        # High confidence
        self.assertTrue(0.85 >= self.ai_responder.confidence_threshold)

        # Low confidence
        self.assertFalse(0.60 >= self.ai_responder.confidence_threshold)
```

**Estimated Time**: 10 hours

---

### Task 12: Create Telegram Tests ✅

**File**: `community_addons/discuss_hub/discuss_hub/tests/test_telegram.py`

**Requirements**:
- [ ] Test send_message()
- [ ] Test receive message webhook
- [ ] Test media handling
- [ ] Mock Telegram API
- [ ] Follow Odoo 18 test patterns

**Estimated Time**: 10 hours

---

## 📋 VALIDATION CHECKLIST

### Before Committing ANY Code

- [ ] ✅ Used `<list>` tag (NOT `<tree>`)
- [ ] ✅ Used `view_mode="list,form"` (NOT "tree,form")
- [ ] ✅ Used `from odoo import Command` for relational fields
- [ ] ✅ Used proper Odoo 18 widgets (badge, etc)
- [ ] ✅ No deprecated patterns from Odoo 17/16/15
- [ ] ✅ Followed existing code style in discuss_hub
- [ ] ✅ Tested in Odoo 18.0 (not older versions)

---

## 🎯 EXECUTION PLAN

### Option 1: QUICK MVP (Recommended for NOW)

**Timeline**: 3 days
**Focus**: Make AI accessible via UI

**Day 1** (8h):
- Create ai_responder_views.xml (6h)
- Update manifest (1h)
- Update security CSV (1h)

**Day 2** (6h):
- Create ai_response_history_views.xml (3h)
- Fix existing view_mode="tree" to "list" (1h)
- Update models/__init__.py (0.5h)
- Update plugins/__init__.py (0.5h)
- Manual testing (1h)

**Day 3** (4h):
- Fix any bugs found (2h)
- Documentation updates (1h)
- Commit and push (1h)

**Result**: AI Responder fully accessible via Odoo 18 UI

---

### Option 2: COMPLETE PHASE 6 (Production Ready)

**Timeline**: 15 days

**Week 1**: Tasks 1-6 (UI & Infrastructure)
**Week 2**: Tasks 7-9 (Missing models)
**Week 3**: Tasks 10-12 (Testing)

**Result**: Full v2.0.0 release

---

## 📊 CRITICAL METRICS

| Item | Status | Odoo 18 Compliant | Priority |
|------|--------|-------------------|----------|
| AI Responder Model | ✅ Done | ✅ Yes | - |
| Telegram Plugin | ✅ Done | ✅ Yes | - |
| AI Views | ❌ Missing | - | 🔴 Critical |
| Security | ❌ Missing | - | 🔴 Critical |
| Manifest | ❌ Outdated | - | 🔴 Critical |
| Tests | ❌ Missing | - | 🟡 Important |

---

## ⚠️ CRITICAL REMINDERS

### DO NOT USE (Odoo 17 and older):
- ❌ `<tree>` tag → Use `<list>`
- ❌ `view_mode="tree"` → Use `view_mode="list"`
- ❌ `widget="statusbar"` → Use `widget="badge"`
- ❌ `(6, 0, [ids])` → Use `Command.set([ids])`
- ❌ Old chatter → Use Odoo 18 pattern

### ALWAYS USE (Odoo 18):
- ✅ `<list>` for list views
- ✅ `view_mode="list,form"`
- ✅ `from odoo import Command`
- ✅ `widget="badge"` for status
- ✅ `widget="boolean_toggle"` for booleans
- ✅ Check existing code in discuss_hub for patterns

---

## 🚀 NEXT ACTION

**Shall I start implementing Phase 6A (Tasks 1-6) following STRICT Odoo 18.0 standards?**

This will create:
1. AI Responder views (proper `<list>` tags)
2. Security rules
3. Updated manifest
4. Fixed all "tree" → "list" references

**Estimated Time**: 12-15 hours
**Timeline**: 2-3 days

All code will follow EXACTLY the patterns in existing discuss_hub files.
