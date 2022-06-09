# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payments Reports - Custom Payments Reports',
    'author': 'EMPAQUES NOVA',
    'version': '1.0.0',
    'category': 'reporting',
    'description': """
        A custom report to get Payments Reports Empaques Nova
    """,
    'depends': [
        'account_reports',
        'payment',
        'informes_invoice',
    ],
    'data': [
        'views/reports_payments.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
