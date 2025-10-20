"""DiscussHub Helpdesk Integration Module.

This module integrates DiscussHub external messaging (WhatsApp, Telegram, etc)
with Odoo's Helpdesk application.

Features:
- Link Helpdesk tickets to DiscussHub channels
- Send WhatsApp messages directly from ticket form
- Track WhatsApp conversation history per ticket
- Automatic channel creation for new tickets
- Priority-based channel naming

License: AGPL-3
"""

from . import models
