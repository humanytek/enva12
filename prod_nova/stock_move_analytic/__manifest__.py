# -*- coding: utf-8 -*-
{
    'name': 'Stock Move Analytic',
    'author': 'EMPAQUES NOVA',
    'website': 'https://www.empaquesnova.com.mx',
    'category': 'Inventory Management',
    'depends': ['stock', 'account', 'stock_account'],
    'version': '14.0.0',
    'license': '',
    'description': """
Include analytic account in stock accounting entries
======================================================
This module adds analytic account field for scrap and
production virtual stock locations.

Also it is posstible to enter analytic account on Stock Picking form.
""",
    'auto_install': False,
    'demo': [],
    'data': [
            'views/analytic_stock_view.xml',
        ],
    'installable': True,
    'application': True,
}
