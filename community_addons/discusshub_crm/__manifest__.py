{
    'name': 'DiscussHub CRM Integration',
    'version': '18.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Integrate DiscussHub (WhatsApp, Telegram) with CRM',
    'description': """
DiscussHub CRM Integration
===========================

This module seamlessly integrates DiscussHub external messaging capabilities
with Odoo's CRM application.

Features
--------
* Link CRM leads and opportunities to DiscussHub channels
* Send WhatsApp messages directly from lead/opportunity form
* Track WhatsApp conversation history per lead
* Automatic channel creation button on lead form
* Custom channel naming based on lead stage and partner
* Message count and last message date on lead
* Smart buttons for quick access to WhatsApp channel

Technical Details
-----------------
* Inherits from discusshub.mixin for standard DiscussHub functionality
* Extends crm.lead model with WhatsApp capabilities
* Adds dedicated "WhatsApp" page in lead form view
* Custom helper methods for CRM-specific behavior

Requirements
------------
* discuss_hub module must be installed
* crm module must be installed
* At least one DiscussHub connector must be configured

Usage
-----
1. Open any CRM Lead or Opportunity
2. Go to "WhatsApp" tab
3. Click "Create WhatsApp Channel" to link a channel
4. Send messages directly from the lead form
5. All WhatsApp messages are tracked in the channel

Author: DiscussHub Community
License: AGPL-3
    """,
    'author': 'DiscussHub Community',
    'website': 'https://github.com/discusshub/discuss_hub',
    'license': 'AGPL-3',
    'depends': [
        'discuss_hub',  # Base DiscussHub module
        'crm',          # CRM application
    ],
    'data': [
        # Security
        # 'security/ir.model.access.csv',  # No new models, no need for access rules

        # Views
        'views/crm_lead_views.xml',

        # Data
        # 'data/automation.xml',  # Optional: automatic actions
    ],
    'demo': [
        # 'demo/demo_data.xml',  # Optional: demo data
    ],
    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': None,
}
