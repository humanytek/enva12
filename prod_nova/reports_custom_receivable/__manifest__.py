# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Receivable Reports - Custom Payments Reports',
    'author': 'ING.JESUS CHULIM',
    'version': '1.0.0',
    'category': 'reporting',
    'description': """
        A custom report to get Receivable Reports Empaques Nova
    """,
    'depends': [
        'account_reports',
        'payment',
        'informes_invoice',
        'account',
        'sale',
        'account_accountant',
        'reports_custom_sales'
    ],
    'data': [
        'views/reports_receipts.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
