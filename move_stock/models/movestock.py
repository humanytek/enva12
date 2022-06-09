# -*- coding: utf-8 -*-
from odoo import api, fields, models
import math

class MoveStock(models.Model):
    _inherit = 'stock.move'

    priceunit = fields.Float(
        string="Precio Unitario",
        compute='_get_price_unit',
        store=True,
    )

    delivered = fields.Float(
        string="Valor Entregado",
        compute='_get_delivered',
        store=True,
    )

    categ_inter = fields.Many2one(
        related='product_tmpl_id.categ_id',
        string="Categoria Interna",
        store=True,
    )

    weight = fields.Float(
        related='product_id.weight',
        string="Peso",
        store=True,
    )

    def _get_price_unit(self):
        for r in self:
            if r.price_unit:
                a = math.fabs(r.price_unit)
                r.priceunit = a

    def _get_delivered(self):
        for r in self:
            if r.price_unit:
                a = math.fabs(r.price_unit)
                r.delivered = a * r.product_uom_qty
