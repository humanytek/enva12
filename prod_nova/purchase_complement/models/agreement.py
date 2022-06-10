# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Newbill(models.Model):
    _inherit = 'purchase.requisition'

    reference = fields.Char(
        string='Referencia',
        store=True,
    )

    anticipo = fields.Char(
        # string='Referencia',
        store=True,
    )

    prioridad = fields.Selection(
        # string="Field name",
        store=True,
        selection=[
                ('0','0'),
                ('1','1'),
                ('2','2'),
                ('3','3'),
        ],
    )
