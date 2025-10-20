"""DiscussHub CRM Integration Module.

This module integrates DiscussHub external messaging (WhatsApp, Telegram, etc)
with Odoo's CRM application.

Features:
- Link CRM leads/opportunities to DiscussHub channels
- Send WhatsApp messages directly from lead form
- Track WhatsApp conversation history per lead
- Automatic channel creation for new leads
- Custom channel naming for leads

License: AGPL-3
"""

from . import models
