# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    def _quantity_in_progress(self):
        res = super(Orderpoint, self)._quantity_in_progress()
        groups = self.env['purchase.order.line'].read_group(
            [('state', 'in', ('draft', 'sent', 'administration','management','to approve')), ('orderpoint_id', 'in', self.ids), ('product_id', 'in', self.mapped('product_id').ids)],
            ['product_id', 'product_qty', 'product_uom', 'orderpoint_id'],
            ['orderpoint_id', 'product_id', 'product_uom'], lazy=False,
        )
        for group in groups:
            orderpoint = self.browse(group['orderpoint_id'][0])
            uom = self.env['uom.uom'].browse(group['product_uom'][0])
            res[orderpoint.id] += uom._compute_quantity(group['product_qty'], orderpoint.product_uom, round=False) if orderpoint.product_id.id == group['product_id'][0] else 0.0
        return res
        super(Orderpoint, self)._quantity_in_progress()
