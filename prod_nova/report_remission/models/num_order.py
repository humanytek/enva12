# -*- coding: utf-8 -*-

from odoo import models, fields


class NumOrder(models.Model):
    _inherit = 'sale.order'

    si_folio = fields.Char(
        string="Folio SI",
        store=True,
     )
