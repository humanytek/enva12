# -*- coding: utf-8 -*-

from odoo import api, fields, models,_

FSC = [
    ('no_aplica', 'No Aplica'),
    ('reciclado', 'Reciclado'),
    ('Mixto', 'Mixto'),
]

class ProductTemplateNova(models.Model):
    _inherit = 'product.template'

    fsc = fields.Selection(
    FSC,
    'FSC',
    track_visibility='onchange',
    # required=True,
    copy=False,
    default='no_aplica'
    )
