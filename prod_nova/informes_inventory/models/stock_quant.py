# -*- coding: utf-8 -*-
from odoo import api, fields, models


class stock_quant_nova(models.Model):
    _inherit= "stock.quant"

    standard_price = fields.Float(
        related='product_tmpl_id.standard_price',
        string='Costo Unitario',

    )

    valuation = fields.Float(
        compute='_get_value',
        string='Valuacion',

    )

    @api.depends('quantity', 'standard_price')
    def _get_value(self):
        for r in self:
            r.valuation= r.quantity*r.standard_price
