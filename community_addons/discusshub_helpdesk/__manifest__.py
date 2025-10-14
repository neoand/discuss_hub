{
    'name': 'DiscussHub Helpdesk Integration',
    'version': '18.0.1.0.0',
    'category': 'Services/Helpdesk',
    'summary': 'Integrate DiscussHub (WhatsApp, Telegram) with Helpdesk',
    'description': """
DiscussHub Helpdesk Integration
================================

Seamlessly integrate DiscussHub external messaging with Odoo Helpdesk.

Features
--------
* Link helpdesk tickets to DiscussHub channels
* Send WhatsApp messages directly from ticket form
* Track WhatsApp conversation history per ticket
* Automatic channel creation on ticket creation
* Priority-based channel naming (Urgent, High, Medium, Low)
* Customer satisfaction surveys via WhatsApp
* SLA tracking with WhatsApp notifications

Requirements
------------
* discuss_hub module
* helpdesk module (Odoo Enterprise or Community alternative)

Author: DiscussHub Community
License: AGPL-3
    """,
    'author': 'DiscussHub Community',
    'website': 'https://github.com/discusshub/discuss_hub',
    'license': 'AGPL-3',
    'depends': [
        'discuss_hub',
        'helpdesk',  # Requires Helpdesk app
    ],
    'data': [
        'views/helpdesk_ticket_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
