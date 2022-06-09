# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Humidity tolerance Purchase',
    'author': 'EMPAQUES NOVA',
    'summary': 'Create humidity tolerance ',
    'category': 'Purchase',
    'description': """
Purchase Humidity Tolerance OCC
    """,
    'depends': [
            'purchase',
            ],
    'data': [

            'views/humidity_tolerance_purchase.xml',
    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,
    'license': '',
}
