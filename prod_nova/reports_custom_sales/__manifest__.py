# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale Reports - Custom Sale Reports',
    'author': 'ING.JESUS CHULIM',
    'version': '1.0.0',
    'category': 'reporting',
    'description': """
        A custom report to get Sale Reports Empaques Nova
    """,
    'depends': [
        'account_reports'
    ],
    'data': [
        'views/reports_sales.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
