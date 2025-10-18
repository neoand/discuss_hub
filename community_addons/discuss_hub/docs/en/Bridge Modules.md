# Bridge Modules - Odoo App Integration 🔗

## 📋 Table of Contents

- [Overview](#overview)
- [DiscussHub Mixin](#discusshub-mixin)
- [CRM Module](#crm-module-discusshub_crm)
- [Helpdesk Module](#helpdesk-module-discusshub_helpdesk)
- [Project Module](#project-module-discusshub_project)
- [Creating Your Own Bridge](#creating-your-own-bridge)
- [Practical Examples](#practical-examples)

---

## 📖 Overview

**Bridge Modules** are extensions that connect existing Odoo applications (CRM, Helpdesk, Project, etc.) with DiscussHub, enabling WhatsApp and other channel communications directly from within records.

### ✨ What Are Bridge Modules?

Modules that extend existing Odoo apps by adding:
- Field to link WhatsApp channel
- Message counters
- Action buttons to send messages
- Integrated conversation history

### 🎯 Benefits

- **Complete Context**: View WhatsApp conversations within the context of Leads, Tickets, or Tasks
- **Quick Communication**: One click to open conversation with customer
- **Centralized History**: All messages recorded in Odoo
- **Automation**: Triggers based on events (stage changes, etc.)

---

## 🧩 DiscussHub Mixin

The **`discusshub.mixin`** is an abstract model that provides ready-to-use functionality for adding messaging to any Odoo model.

### 📦 What the Mixin Adds

#### Automatic Fields

```python
# Relationship field
discusshub_channel_id = fields.Many2one('discuss.channel')
# Link to the WhatsApp/Telegram channel linked to this record

# Computed fields
discusshub_message_count = fields.Integer(compute='_compute_discusshub_message_count')
# Number of messages in the linked channel

discusshub_last_message_date = fields.Datetime(compute='_compute_discusshub_message_count')
# Date of last received/sent message
```

#### Automatic Methods

```python
# Open conversation to send message
record.action_send_discusshub_message()

# Create and link new WhatsApp channel
record.action_create_discusshub_channel()

# Open existing channel
record.action_open_discusshub_channel()
```

#### Helper Methods (To Override)

```python
# Get phone number from record
def _get_discusshub_destination(self):
    """Returns number in format '5511999999999'"""

# Get channel name
def _get_discusshub_channel_name(self):
    """Returns name like 'WhatsApp: Lead - Customer XYZ'"""
```

---

## 📦 Available Modules

### 🎯 CRM Integration (`discusshub_crm`)

**Location**: `community_addons/discusshub_crm/`
**Lines of Code**: ~450 LOC
**Status**: ✅ Production

#### Features

- Link WhatsApp channels to Leads and Opportunities
- Send messages directly from Lead form
- Track conversation history
- Auto-detect phone (partner or lead fields)
- Naming based on lead stage

#### Files

```
community_addons/discusshub_crm/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── crm_lead.py          # Extensions to crm.lead model
└── views/
    └── crm_lead_views.xml   # Buttons and fields in view
```

#### Installation

```bash
# Via Odoo interface
Apps → Search "DiscussHub CRM" → Install

# Via command line
odoo -u discusshub_crm -d database_name
```

#### Basic Usage

```python
# Get lead
lead = env['crm.lead'].browse(1)

# Create WhatsApp channel for lead
lead.action_create_discusshub_channel()
# This automatically creates a channel linked to partner's phone

# Send message
lead.action_send_discusshub_message()
# Opens channel to send message

# Access information
print(lead.discusshub_message_count)      # Ex: 15 messages
print(lead.discusshub_last_message_date)  # Ex: 2025-10-17 14:30:00
```

#### Customization

```python
# Override channel naming
class Lead(models.Model):
    _inherit = 'crm.lead'

    def _get_discusshub_channel_name(self):
        """Custom name based on stage"""
        stage = self.stage_id.name if self.stage_id else 'New'
        return f"WhatsApp: [{stage}] {self.name}"

    def _get_discusshub_destination(self):
        """Prioritize partner's mobile"""
        if self.partner_id and self.partner_id.mobile:
            return self.partner_id.mobile
        elif self.phone:
            return self.phone
        return super()._get_discusshub_destination()
```

#### View XML

The module adds a button to the Lead form:

```xml
<xpath expr="//div[@name='button_box']" position="inside">
    <button name="action_create_discusshub_channel"
            type="object"
            class="oe_stat_button"
            icon="fa-whatsapp"
            attrs="{'invisible': [('discusshub_channel_id', '!=', False)]}">
        <div class="o_field_widget o_stat_info">
            <span class="o_stat_text">Create</span>
            <span class="o_stat_text">WhatsApp</span>
        </div>
    </button>

    <button name="action_open_discusshub_channel"
            type="object"
            class="oe_stat_button"
            icon="fa-whatsapp"
            attrs="{'invisible': [('discusshub_channel_id', '=', False)]}">
        <field name="discusshub_message_count" widget="statinfo" string="Messages"/>
    </button>
</xpath>
```

---

### 🎫 Helpdesk Integration (`discusshub_helpdesk`)

**Location**: `community_addons/discusshub_helpdesk/`
**Lines of Code**: ~200 LOC
**Status**: ✅ Production

#### Features

- Link WhatsApp channels to support tickets
- Reply to customers via WhatsApp from ticket form
- Track support conversations
- Auto-detect customer phone
- Integration with SLA and priorities

#### Files

```
community_addons/discusshub_helpdesk/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── helpdesk_ticket.py    # Extensions to helpdesk.ticket model
└── views/
    └── helpdesk_ticket_views.xml
```

#### Installation

```bash
# Prerequisite: helpdesk module installed
# Apps → Search "DiscussHub Helpdesk" → Install

odoo -u discusshub_helpdesk -d database_name
```

#### Basic Usage

```python
# Get ticket
ticket = env['helpdesk.ticket'].browse(1)

# Create WhatsApp channel
ticket.action_create_discusshub_channel()

# Send message to customer
ticket.action_send_discusshub_message()

# Access statistics
print(f"Messages: {ticket.discusshub_message_count}")
print(f"Last message: {ticket.discusshub_last_message_date}")
```

#### Use Case: Customer Support

```python
# When ticket is created, create channel automatically
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super().create(vals_list)

        for ticket in tickets:
            # If customer has WhatsApp, create channel
            if ticket.partner_id and (ticket.partner_id.mobile or ticket.partner_id.phone):
                try:
                    ticket.action_create_discusshub_channel()
                except Exception as e:
                    _logger.warning(f"Could not create WhatsApp channel: {e}")

        return tickets
```

#### Message Automation

```python
# Send automatic message when ticket is resolved
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def write(self, vals):
        result = super().write(vals)

        # If changed to "Resolved" stage
        if vals.get('stage_id'):
            stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            if stage.is_close:
                self._send_resolution_message()

        return result

    def _send_resolution_message(self):
        """Send ticket resolved message"""
        if not self.discusshub_channel_id:
            return

        # Use template
        template = self.env.ref('discusshub_helpdesk.template_ticket_resolved')
        message = template.render(ticket=self)

        # Send via channel
        self.discusshub_channel_id.message_post(
            body=message,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
```

---

### 📋 Project Integration (`discusshub_project`)

**Location**: `community_addons/discusshub_project/`
**Lines of Code**: ~150 LOC
**Status**: ✅ Production

#### Features

- Link WhatsApp channels to project tasks
- Communicate with clients about task progress
- Track task-related conversations
- Notifications for assignees/followers
- Status updates via WhatsApp

#### Files

```
community_addons/discusshub_project/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── project_task.py       # Extensions to project.task model
└── views/
    └── project_task_views.xml
```

#### Installation

```bash
# Apps → Search "DiscussHub Project" → Install
odoo -u discusshub_project -d database_name
```

#### Basic Usage

```python
# Get task
task = env['project.task'].browse(1)

# Create WhatsApp channel
task.action_create_discusshub_channel()

# Send update to client
task.action_send_discusshub_message()
```

#### Use Case: Progress Updates

```python
class ProjectTask(models.Model):
    _inherit = 'project.task'

    def write(self, vals):
        result = super().write(vals)

        # Notify client when task is completed
        if vals.get('stage_id'):
            stage = self.env['project.task.type'].browse(vals['stage_id'])
            if stage.fold:  # Final stage
                self._notify_task_completion()

        return result

    def _notify_task_completion(self):
        """Notify client via WhatsApp"""
        if not self.discusshub_channel_id:
            return

        message = f"""
🎉 *Task Completed!*

Hello {self.partner_id.name},

The task *{self.name}* has been successfully completed!

📋 *Details:*
- Project: {self.project_id.name}
- Assignee: {self.user_ids[0].name if self.user_ids else 'N/A'}
- Completion date: {fields.Date.today()}

If you have any questions, we're here to help!

Best regards,
{self.env.company.name}
        """

        self.discusshub_channel_id.message_post(
            body=message,
            message_type='comment',
        )
```

---

## 🛠️ Creating Your Own Bridge

Follow this guide to integrate DiscussHub with any Odoo module.

### Step 1: Module Structure

```bash
mkdir community_addons/discusshub_custom
cd community_addons/discusshub_custom

# Create structure
mkdir models views
touch __init__.py __manifest__.py README.md
touch models/__init__.py models/custom_model.py
touch views/custom_model_views.xml
```

### Step 2: Manifest (`__manifest__.py`)

```python
{
    'name': 'DiscussHub Custom Integration',
    'version': '18.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Integrate DiscussHub with Custom Module',
    'depends': [
        'discuss_hub',           # DiscussHub base module
        'your_custom_module',    # Your module to integrate
    ],
    'data': [
        'views/custom_model_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
```

### Step 3: Model (`models/custom_model.py`)

```python
from odoo import models, api

class CustomModel(models.Model):
    _name = 'your.custom.model'
    _inherit = ['your.custom.model', 'discusshub.mixin']

    # Done! Your model now has all mixin fields and methods

    # (Optional) Customize phone detection
    def _get_discusshub_destination(self):
        """Get custom phone"""
        if self.custom_phone_field:
            return self.custom_phone_field
        return super()._get_discusshub_destination()

    # (Optional) Customize channel name
    def _get_discusshub_channel_name(self):
        """Custom channel name"""
        return f"WhatsApp: {self.name} - {self.state}"
```

### Step 4: View (`views/custom_model_views.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_custom_model_form_inherit_discusshub" model="ir.ui.view">
        <field name="name">your.custom.model.form.inherit.discusshub</field>
        <field name="model">your.custom.model</field>
        <field name="inherit_id" ref="your_module.view_custom_model_form"/>
        <field name="arch" type="xml">

            <!-- Add buttons in button_box -->
            <xpath expr="//div[@name='button_box']" position="inside">

                <!-- Button: Create Channel -->
                <button name="action_create_discusshub_channel"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-whatsapp"
                        attrs="{'invisible': [('discusshub_channel_id', '!=', False)]}">
                    <div class="o_field_widget o_stat_info">
                        <span class="o_stat_text">Create</span>
                        <span class="o_stat_text">WhatsApp</span>
                    </div>
                </button>

                <!-- Button: Open Channel (with counter) -->
                <button name="action_open_discusshub_channel"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-whatsapp"
                        attrs="{'invisible': [('discusshub_channel_id', '=', False)]}">
                    <field name="discusshub_message_count"
                           widget="statinfo"
                           string="Messages"/>
                </button>

            </xpath>

            <!-- (Optional) Add fields in form -->
            <xpath expr="//sheet" position="inside">
                <group string="DiscussHub">
                    <field name="discusshub_channel_id" readonly="1"/>
                    <field name="discusshub_message_count" readonly="1"/>
                    <field name="discusshub_last_message_date" readonly="1"/>
                </group>
            </xpath>

        </field>
    </record>
</odoo>
```

### Step 5: Initialization (`__init__.py`)

```python
from . import models
```

```python
# models/__init__.py
from . import custom_model
```

### Step 6: Installation

```bash
# Restart Odoo
docker compose restart odoo

# Install module
# Apps → Update Apps List → Search "DiscussHub Custom" → Install
```

---

## 💡 Practical Examples

### Example 1: Auto-create Channel When Creating Record

```python
class CustomModel(models.Model):
    _inherit = 'your.custom.model'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for record in records:
            # If has partner with phone, create channel automatically
            if record.partner_id and record.partner_id.mobile:
                record.action_create_discusshub_channel()

        return records
```

### Example 2: Send Automatic Message on Event

```python
class CustomModel(models.Model):
    _inherit = 'your.custom.model'

    def action_confirm(self):
        """On confirm, send message via WhatsApp"""
        result = super().action_confirm()

        for record in self:
            if record.discusshub_channel_id:
                message = f"""
Hello {record.partner_id.name}!

Your request *{record.name}* has been confirmed.

Status: ✅ Confirmed
Date: {fields.Date.today()}

Thank you!
                """
                record.discusshub_channel_id.message_post(
                    body=message,
                    message_type='comment',
                )

        return result
```

### Example 3: Use Jinja2 Templates

```python
class CustomModel(models.Model):
    _inherit = 'your.custom.model'

    def send_status_update(self):
        """Send update using template"""
        template = self.env.ref('discusshub_custom.template_status_update')

        for record in self:
            if not record.discusshub_channel_id:
                continue

            # Render template
            message = template.render(
                record=record,
                partner=record.partner_id,
                company=self.env.company,
            )

            # Send
            record.discusshub_channel_id.message_post(
                body=message,
                message_type='comment',
            )
```

### Example 4: Integration with Automated Triggers

```python
# Create automatic trigger via code
trigger = env['discuss_hub.automated_trigger'].create({
    'name': 'Notify Stage Change - Custom',
    'model_id': env.ref('your_module.model_your_custom_model').id,
    'trigger_type': 'on_stage_change',
    'stage_to_id': env.ref('your_module.stage_done').id,
    'template_id': env.ref('discusshub_custom.template_stage_done').id,
    'active': True,
})
```

### Example 5: Custom Widget

```xml
<!-- Add inline chat widget -->
<xpath expr="//sheet" position="after">
    <div class="oe_chatter">
        <field name="discusshub_channel_id" widget="mail_thread"
               options="{'display_log_button': True}"/>
    </div>
</xpath>
```

---

## 🎓 Best Practices

### 1. Always Check if Channel Exists

```python
if record.discusshub_channel_id:
    # Do something
else:
    _logger.warning(f"Record {record} doesn't have WhatsApp channel")
```

### 2. Error Handling

```python
try:
    record.action_create_discusshub_channel()
except Exception as e:
    _logger.error(f"Error creating channel: {e}")
    # Don't break main flow
```

### 3. Verify Phone Before Creating Channel

```python
def create_channel_if_phone_exists(self):
    if not self._get_discusshub_destination():
        raise UserError("Record doesn't have valid phone number")
    return self.action_create_discusshub_channel()
```

### 4. Use Context for Control

```python
# Create without notifying
record.with_context(no_discusshub_notification=True).write({'state': 'done'})
```

### 5. Proper Logging

```python
import logging
_logger = logging.getLogger(__name__)

_logger.info(f"WhatsApp channel created for {record.name}")
_logger.warning(f"Phone not found for {record.name}")
_logger.error(f"Failed to send message: {error}")
```

---

## 📚 References

- [DiscussHub Mixin - Source Code](../../discuss_hub/models/discusshub_mixin.py)
- [Odoo Documentation - Mixins](https://www.odoo.com/documentation/18.0/developer/reference/backend/mixins.html)
- [Automated Triggers](./Automated%20Triggers.md)
- [Message Templates](./Message%20Templates.md)

---

## ❓ FAQ

### Q: Can I use the mixin in transient models?

**A**: Not recommended. The mixin was designed for persistent models (models.Model), not wizards (models.TransientModel).

### Q: How to add extra fields to the channel?

**A**: Override `action_create_discusshub_channel()`:

```python
def action_create_discusshub_channel(self):
    res = super().action_create_discusshub_channel()

    # Add extra fields
    self.discusshub_channel_id.write({
        'custom_field': self.custom_value,
    })

    return res
```

### Q: Can I have multiple channels per record?

**A**: The default mixin supports only one channel. For multiple channels, you'd need to create custom One2many fields.

### Q: How to disable automatic channel creation?

**A**: Remove the `action_create_discusshub_channel()` call from the `create()` method or add a condition:

```python
if not self.env.context.get('skip_discusshub_creation'):
    record.action_create_discusshub_channel()
```

---

**Documentation created on**: October 17, 2025
**Version**: 1.0.0
**Compatibility**: Odoo 18.0+, DiscussHub 18.0.1.0.0+
