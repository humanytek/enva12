# -*- coding: utf-8 -*-
{
    'name': 'Indicators',
    'author': 'EMPAQUES NOVA',
    'website': 'http://www.empaquesnova.com.mx',
    'category': 'Purchase',
    'version': '1.0.0',
    'depends': [
        'account_reports',
        'nova_account_bank_statement'
    ],
    'data': [
        'views/indicators.xml',

    ],
     'application': True,
}