# -*- coding: utf-8 -*-
{
    'name': 'Human Resources Requisition',
    'author': 'EMPAQUES NOVA',
    'website': 'http://www.empaquesnova.com.mx',
    'category': 'Human Resources',
    'version': '1.0.0',
    'depends': [
        'hr',
        'hr_recruitment',
        'account',
    ],
    'data': [
    'views/rh_requisition.xml',
    'views/rh_salary_report.xml',
    'views/rh_change_nomenclature.xml',
    'reports/salary_report.xml',

    ],
     'application': True,
}
