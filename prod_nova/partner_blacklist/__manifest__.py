# -*- coding: utf-8 -*-
{
    'name': 'Partner LIST 69-b  SAT',
    'author': 'EMPAQUES NOVA, ING.JESUS CHULIM',
    'website': 'http://www.empaquesnova.com.mx',
    'category': 'Partner',
    'version': '1.0.0',
    'summary': """
Partner list 69-B  SAT accounting from mexico
""",
    'depends': [
    'account',
    'base',
    'sale',
    'account_reports',
    'account_accountant',
    'purchase',
    'informes_partner_invoice',
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'views/blacklist.xml',
    ],
     'application': True,
}
