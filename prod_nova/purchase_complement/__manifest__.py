# -*- coding: utf-8 -*-
{
    'name': 'Purchase Complement Nova',
    'author': 'EMPAQUES NOVA isc_dcm',
    'website': 'http://www.empaquesnova.com.mx',
    'category': 'Uncategorized',
    'version': '1.0.0',
    'depends': [
        'purchase',
        'sale_management',
        'purchase_user_validation',
    ],
    'data': [
        'reports/orden.xml',
        'views/to_receive.xml',
        'views/analysis.xml',
        'views/requisition.xml',
        'views/agreement.xml',
        'reports/licitacion.xml',
    ],
}
