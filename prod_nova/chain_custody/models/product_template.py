# -*- coding: utf-8 -*-

from odoo import api, fields, models,_

FSC = [
    ('no_aplica', 'No Aplica'),
    ('reciclado', 'Reciclado'),
    ('mixto', 'Mixto'),
]

FSC_TIPO = [
    ('papel', 'Papel Kraft'),
    ('lamina', 'Laminas de Cartón'),
    ('caja', 'Empaques de Cartón'),
]

class ProductTemplateNova(models.Model):
    _inherit = 'product.template'

    fsc = fields.Selection(
    FSC,
    'FSC',
    track_visibility='onchange',
    copy=False,
    default='no_aplica'
    )

    fsc_tipo = fields.Selection(
    FSC_TIPO,
    'Tipo',
    track_visibility='onchange',
    copy=False,
    )
