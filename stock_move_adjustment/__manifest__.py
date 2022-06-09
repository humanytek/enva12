# -*- coding: utf-8 -*-
{
    'name': 'Stock Move Adjustment',
    'author': 'EMPAQUES NOVA',
    'website': 'http://www.empaquesnova.com.mx',
    'category': 'Inventory Management',
    'depends': ['stock', 'account', 'stock_account'],
    'description': """
Creates the account move according the stablished date for exchange calculation
===============================================================================
This module adds a date for every incoming stock picking and calculates  according to exchange rate date

""",
    'auto_install': False,
    'demo': [],
    'data': ['views/stock_picking_view.xml'],
    'installable': True,
    'application': True,
}
