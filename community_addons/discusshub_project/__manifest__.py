{
    'name': 'DiscussHub Project Integration',
    'version': '18.0.1.0.0',
    'category': 'Services/Project',
    'summary': 'Integrate DiscussHub (WhatsApp) with Project Tasks',
    'author': 'DiscussHub Community',
    'website': 'https://github.com/discusshub/discuss_hub',
    'license': 'AGPL-3',
    'depends': [
        'discuss_hub',
        'project',
    ],
    'data': [
        'views/project_task_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
