# DiscussHub CRM Integration

**Version**: 18.0.1.0.0
**Category**: Sales/CRM
**License**: AGPL-3

## 📋 Description

This module seamlessly integrates **DiscussHub** external messaging capabilities (WhatsApp, Telegram, etc.) with Odoo's **CRM** application.

Communicate with your leads and opportunities directly via WhatsApp without leaving Odoo!

---

## ✨ Features

### 🎯 Core Functionality
- ✅ **Link WhatsApp channels to CRM leads/opportunities**
- ✅ **Send WhatsApp messages directly from lead form**
- ✅ **Track WhatsApp conversation history per lead**
- ✅ **Automatic channel creation with smart button**
- ✅ **Custom channel naming** based on lead stage and partner
- ✅ **Real-time message synchronization**

### 📊 UI Enhancements
- ✅ **Smart button** in lead header showing message count
- ✅ **Dedicated "WhatsApp" tab** in lead form
- ✅ **WhatsApp indicator column** in tree view
- ✅ **WhatsApp badge** in kanban cards
- ✅ **Search filters**: "With WhatsApp", "Without WhatsApp"
- ✅ **Group by WhatsApp status**

### 🔧 Technical Features
- ✅ **Inherits from `discusshub.mixin`** for standard functionality
- ✅ **Custom phone detection logic** (partner mobile > partner phone > lead mobile > lead phone)
- ✅ **Automatic phone number cleaning** (removes formatting)
- ✅ **CRM-specific channel naming**: `[Stage] Lead Name - Partner Name`
- ✅ **Logging and error handling**

---

## 📦 Requirements

### Dependencies
- `discuss_hub` — Base DiscussHub module
- `crm` — Odoo CRM application

### Configuration
- At least **one DiscussHub connector** must be configured (Settings → Technical → DiscussHub Connectors)
- Leads/contacts must have **valid phone numbers** (mobile preferred)

---

## 🚀 Installation

### 1. Install Module
```bash
# Via Odoo CLI
odoo-bin -i discusshub_crm -d your_database

# Via Odoo UI
Apps → Search "DiscussHub CRM" → Install
```

### 2. Configure DiscussHub Connector
1. Go to **Settings → Technical → DiscussHub → Connectors**
2. Create or verify your Evolution API connector
3. Ensure connector is **enabled**

### 3. Verify Installation
1. Open any **CRM Lead**
2. You should see a new **"WhatsApp" tab**
3. Click **"Create WhatsApp Channel"** to test

---

## 📖 Usage Guide

### Create WhatsApp Channel for Lead

1. **Open CRM Lead/Opportunity**
   - Go to `CRM → Leads` or `CRM → Pipeline`
   - Open any lead with a contact that has a phone number

2. **Navigate to WhatsApp Tab**
   - Click on the **"WhatsApp"** tab in the lead form

3. **Create Channel**
   - Click the **"Create WhatsApp Channel"** button
   - Channel is automatically created and linked
   - Phone number is detected from partner or lead fields

4. **Send Messages**
   - Click **"Send Message"** to open the WhatsApp channel
   - Type your message in the chatter
   - Message is automatically sent via WhatsApp!

### View WhatsApp Messages

#### Option 1: From Lead Form
- Open lead → **WhatsApp tab** → **"Open Channel"** button

#### Option 2: Smart Button
- Click the **WhatsApp smart button** in the lead header (shows message count)

#### Option 3: Discuss App
- Open **Discuss** app
- Find the channel in the channels list
- Channel name format: `WhatsApp: [Stage] Lead Name - Partner Name`

### Filter Leads by WhatsApp Status

#### Tree View
- Enable **"WhatsApp"** column (optional columns)
- Green checkmark = channel linked
- Empty = no channel

#### Search/Filters
- Use **"With WhatsApp"** filter to see leads with channels
- Use **"Without WhatsApp"** filter to see leads needing setup
- **Group by → WhatsApp Status** to organize leads

#### Kanban View
- Look for **green "WhatsApp" badge** on cards

---

## 🔧 Technical Details

### Model Extension

```python
class Lead(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', 'discusshub.mixin']
```

### Fields Added

| Field | Type | Description |
|-------|------|-------------|
| `discusshub_channel_id` | Many2one | Link to discuss.channel |
| `discusshub_message_count` | Integer | Number of WhatsApp messages |
| `discusshub_last_message_date` | Datetime | Last message timestamp |

### Methods Added

| Method | Description |
|--------|-------------|
| `action_create_discusshub_channel()` | Create and link WhatsApp channel |
| `action_send_discusshub_message()` | Open channel to send message |
| `action_open_discusshub_channel()` | Open channel in new window |
| `_get_discusshub_destination()` | Get phone number (custom CRM logic) |
| `_get_discusshub_channel_name()` | Get channel name (CRM format) |

### Phone Number Detection Logic

```python
Priority order:
1. partner_id.mobile      # Preferred for WhatsApp
2. partner_id.phone       # Landline fallback
3. lead.mobile            # Lead's mobile field
4. lead.phone             # Lead's phone field
```

### Channel Naming Format

```python
Format: "WhatsApp: [Stage] Lead Name - Partner Name"

Examples:
- "WhatsApp: [New] John Doe Inquiry - John Doe"
- "WhatsApp: [Qualified] ABC Corp Opportunity - ABC Corp"
- "WhatsApp: [Won] Enterprise Deal - Big Client Inc"
```

---

## 🎨 Screenshots

### Lead Form - WhatsApp Tab
![WhatsApp Tab](static/description/screenshot_lead_form.png)

### Smart Button
![Smart Button](static/description/screenshot_smart_button.png)

### Kanban View
![Kanban Badge](static/description/screenshot_kanban.png)

---

## 🐛 Known Issues / Limitations

### Current Limitations
1. **Phone number format**: Must be in international format (e.g., `5511999999999`)
2. **Single connector**: Uses first enabled Evolution connector (no per-lead connector selection)
3. **No templates**: Template selection wizard not yet implemented

### Planned Features
- ✨ WhatsApp template selection wizard
- ✨ Bulk WhatsApp messaging for campaigns
- ✨ WhatsApp activity logging in CRM timeline
- ✨ Per-lead connector selection
- ✨ Automatic channel creation on lead convert

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/discusshub/discuss_hub.git

# Navigate to CRM module
cd discuss_hub/discusshub_crm

# Install in development mode
odoo-bin -i discusshub_crm -d dev_database --dev=all
```

---

## 📄 License

**AGPL-3**

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

---

## 👥 Credits

### Authors
- **DiscussHub Community**

### Contributors
- Your Name <your.email@example.com>

### Maintainer
This module is maintained by the DiscussHub Community.

---

## 📞 Support

- **Documentation**: [https://github.com/discusshub/discuss_hub/wiki](https://github.com/discusshub/discuss_hub/wiki)
- **Issues**: [https://github.com/discusshub/discuss_hub/issues](https://github.com/discusshub/discuss_hub/issues)
- **Forum**: [https://www.odoo.com/forum](https://www.odoo.com/forum)

---

## 🔗 Related Modules

- **`discuss_hub`** — Base DiscussHub module
- **`discusshub_helpdesk`** — DiscussHub Helpdesk integration
- **`discusshub_project`** — DiscussHub Project integration
- **`discusshub_sale`** — DiscussHub Sales integration

---

**Made with ❤️ by the DiscussHub Community**
