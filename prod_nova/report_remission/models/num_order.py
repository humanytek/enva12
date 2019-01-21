# -*- coding: utf-8 -*-

from odoo import models, fields


class NumOrder(models.Model):
    _inherit = 'sale.order'

    num_order_id = fields.Char(
        string='Order Number',
        store=True,
    )
