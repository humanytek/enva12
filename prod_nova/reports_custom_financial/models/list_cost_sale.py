# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

class ListCostSaleNova(models.Model):
    _name = 'list.cost.sale.nova'

    name = fields.Char(
        'Nombre Costo de Venta',
        required = True,
        store = True,
    )
