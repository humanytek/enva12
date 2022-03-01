# -*- coding: utf-8 -*-
{
    'name': 'Maintenance Requisition',
    'author': 'EMPAQUES NOVA','ING.JESUS CHULIM'
    'website': 'http://www.empaquesnova.com.mx',
    'category': 'Maintenance',
    'version': '1.0.0',
    'depends': [
        'maintenance',
        'maintenance_plan',
        'maintenance_request_stage_transition',
        'maintenance_request_sequence',
        'purchase_requisition',
    ],
    'data': [
        'views/maintenance_requisition.xml',
    ],
     'application': True,
}
