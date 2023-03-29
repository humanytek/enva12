# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Bank Statements',
    'author': 'EMPAQUES NOVA',
    'version': '1.0.0',
    'category': 'accounting',
    'description': """
        A custom report to get Bank Statements Empaques Nova
    """,
    'depends': [
        'account',
    ],
    'data': [
        'views/account_bank_statement_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}