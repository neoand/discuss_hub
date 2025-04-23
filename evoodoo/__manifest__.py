{
    "name": "evoodoo",
    "summary": "Third Party Messsage integration for Odoo's Discuss Channel",
    "author": "Duda Nogueira",
    "website": "https://github.com/dudanogueira/evoodoo",
    "category": "marketing",
    "version": "18.0.0.0.4",
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
        # initial base_automation
        "datas/base_automation.xml",
        # wizards
        "wizard/mail_discuss_channel_forward.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "evoodoo/static/src/js/discuss_channel_actions.esm.js",
        ],
    },
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
}
