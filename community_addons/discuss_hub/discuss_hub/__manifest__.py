{
    "name": "discuss_hub",
    "summary": "Third Party Messsage integration for Odoo's Discuss Channel",
    "author": "Discuss Hub Community",
    "website": "https://github.com/discusshub/discuss_hub",
    "category": "marketing",
    "version": "18.0.3.0.0",
    "license": "AGPL-3",
    "application": True,
    "installable": True,
    # any module necessary for this one to work correctly
    "depends": ["base", "mail", "base_automation", "crm"],
    # always loaded
    "data": [
        #'security/security.xml',
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/templates.xml",
        "views/res_partner_view.xml",
        # Phase 3: Templates system
        "views/message_template_views.xml",
        # Phase 3 Advanced: Bulk send wizard
        "views/bulk_send_wizard_views.xml",
        # Phase 3 Advanced: Analytics dashboard
        "views/analytics_views.xml",
        # Phase 3 Advanced: Automated triggers
        "views/automated_trigger_views.xml",
        # Phase 5-6: AI Features with Multi-Provider Support
        "views/ai_responder_views.xml",
        "views/ai_response_history_views.xml",
        "views/sentiment_analyzer_views.xml",
        "views/voice_message_views.xml",
        # initial base_automation
        "datas/base_automation.xml",
        # wizards
        "wizard/mail_discuss_channel_forward.xml",
        "wizard/mail_discuss_channel_archive.xml",
        "wizard/ai_setup_wizard_views.xml",
        "wizard/telegram_setup_wizard_views.xml",
    ],
    "external_dependencies": {
        "python": [
            "google-generativeai",
            "textblob",
            "SpeechRecognition",
            "pydub",
        ],
    },
    "assets": {
        "web.assets_backend": [
            "discuss_hub/static/src/js/discuss_channel_actions.esm.js",
        ],
    },
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
        "data/message_templates.xml",  # Phase 3: Demo templates
    ],
}
