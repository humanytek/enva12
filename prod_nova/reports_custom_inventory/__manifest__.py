# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Reports Inventory',
    'author': 'EMPAQUES NOVA',
    'version': '1.0',
    'category': 'reporting',
    'description': """
        A custom report to get Stock Products Empaques Nova
    """,
    'depends': [
        'base_setup', 'product','account_reports',  
    ],
    'data': [
         'views/partner.xml',
         'views/product_template.xml',
         'views/reports_custom_inv.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}