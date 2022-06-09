# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale Reports - Custom Sale Reports',
    'author': 'EMPAQUES NOVA',
    'version': '1.5.0',
    'category': 'reporting',
    'description': """
        A custom report to get Sale Reports Empaques Nova
    """,
    'depends': [
        'account_reports',
        'informes_invoice',
    ],
    'data': [
        'views/reports_sales.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
