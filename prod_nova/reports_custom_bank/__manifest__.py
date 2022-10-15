# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Bank Reports - Custom Bank Reports',
    'author': 'EMPAQUES NOVA',
    'version': '1.0.0',
    'category': 'reporting',
    'description': """
        A custom report to get Bank Reports Empaques Nova
    """,
    'depends': [
        'account_reports',
    ],
    'data': [
        'views/bank_reports.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
