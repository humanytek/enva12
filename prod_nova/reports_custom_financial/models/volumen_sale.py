# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

NAME_VOLUMEN_SALE=[
('TONELADAS FACTURADAS CAJAS','TONELADAS FACTURADAS CAJAS'),
('TONELADAS FACTURADAS PAPEL','TONELADAS FACTURADAS PAPEL')
]

class VolumenSales(models.Model):
    _name = 'volumen.sales'


    name = fields.Selection(
        NAME_VOLUMEN_SALE,
        'NOMBRE VOLUMEN DE VENTAS',
        required=True,
        store=True,
    )

    date_from=fields.Date(
        string='Date From',
        required=True,
        store=True,
    )

    date_to=fields.Date(
        string='Date To',
        required=True,
        store=True,
    )

    ton_per_month=fields.Float(
    string='Tonelada mes',
    store=True,
    )

    ton_per_month_budget=fields.Float(
    string='Tonelada mes Presupuesto',
    store=True,
    )
