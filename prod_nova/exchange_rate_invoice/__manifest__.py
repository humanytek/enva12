# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Tipo de cambio para factura',
    'version' : '14',
    'summary': 'Utiliza el tipo de cambio de la fecha de contabilizacion o la del día para generar los asientos y agrega fecha de contabilizacion del día de creación ',
    'sequence': 100,
    'description': """
Personalizacion del tipo de cambio al facturar
=============================================
Se asegura que el tipo de cambio usado sea del de la fecha factura. Si no se establece, se usa la fecha de contabilizacion o se usa la fecha del día.
    """,
    'category' : 'Accounting & Finance',
    'website': 'http://www.empaquesnova.com.mx/',
    'images' : [],
    'author': 'Empaques Nova',
    'depends' : ['account'],
    'data': [
        ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
