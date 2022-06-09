# -*- coding: utf-8 -*-
{
    'name': 'Work Receipts',
    'author': 'EMPAQUES NOVA',
    'website': 'http://www.empaquesnova.com.mx',
    'category': 'Purchase',
    'version': '1.0.1',
    'depends': [
    'purchase',
    'account',
    ],
    'data': [
        'views/receipts.xml',
        'reports/report_receipts.xml',
        'data/mail_template_data_work.xml',
    ],
     'application': True,
}
