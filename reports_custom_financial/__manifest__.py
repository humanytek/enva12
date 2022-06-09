# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Accounting Reports - Custom Financial Reports',
    'author': 'EMPAQUES NOVA',
    'version': '2.5',
    'category': 'reporting',
    'description': """
        A custom report to get Financial Reports Empaques Nova
    """,
    'depends': [
        'account',
        'account_reports',
    ],
    'data': [
        'views/custom_financial_reports.xml',
        'views/custom_reports_group.xml',
        'views/budget_nova.xml',
        'views/budget_results.xml',
        'views/list_cost_sale.xml',
        'views/cost_sale.xml',
        'views/sale_volumen.xml',
        'views/account_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
