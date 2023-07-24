# -*- coding: utf-8 -*-

from odoo import api, fields, models,_

FSC = [
    ('no_aplica', 'No Aplica'),
    ('reciclado', 'FSC RECICLADO 100%'),
    ('mixto', 'FSC MIXTO'),
]

FSC_TIPO = [
    ('papel', 'Papel Kraft'),
    ('lamina', 'Laminas de Cartón'),
    ('caja', 'Empaques de Cartón'),
]
PORCENT_MIXTO = [
    ('50','50%'),
    ('60','60%'),
    ('70','70%'),
    ('80','80%'),
    ('90','90%'),
]

class ProductTemplateNova(models.Model):
    _inherit = 'product.template'

    fsc = fields.Selection(
        FSC,
        'FSC',
        tracking=True,
        # required=True,
        copy=False,
        default='no_aplica'
    )


    fsc_tipo = fields.Selection(
        FSC_TIPO,
        'Tipo',
        tracking=True,
        copy=False,
    )

    porcent_mixto = fields.Selection(
        PORCENT_MIXTO,
        'Porcentaje',
        tracking=True,
        copy=False,
    )