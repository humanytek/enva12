# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseAnalysis(models.Model):
    _inherit = 'purchase.order.line'

    date_order = fields.Datetime(
        related='order_id.date_order',
        # string='Acuerdo Compra',
    )

    origin = fields.Char(
        related='order_id.origin',
        string='Referencia del proveedor',
    )

    responsable = fields.Many2one(
        related='order_id.user_id',
        string='Responsable',
        store=True,
    )
