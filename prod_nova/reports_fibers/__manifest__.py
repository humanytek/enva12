# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Reports Fibers',
    'author': 'EMPAQUES NOVA',
    'version': '1.0.0',
    'category': 'reporting',
    'description': """
        A custom report to get Reports Fibers Empaques Nova
    """,
    'depends': [
        'account_reports',

    ],
    'data': [
        'views/reports_fibers.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
