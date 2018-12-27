# -*- coding: utf-8 -*-
{
    'name': 'Informes Invoice',
    'author': 'EMPAQUES NOVA',
    'website': 'http://www.empaquesnova.com.mx',
    'category': 'Uncategorized',
    'version': '1.0.0',
    'depends': [
        'account',
        'sale',
        'account_reports',
        'account_accountant',
    ],
    'data': [
        'reports/invoice_reports_sale.xml',
        'views/account_invoice_nova.xml',
        'views/account_invoice_line.xml',
    ],
}
