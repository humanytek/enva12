# -*- coding: utf-8 -*-

from odoo import api, fields, models,_


class ProductTemplateNova(models.Model):
    _inherit = 'product.template'

    partner_cus_id= fields.Many2one(
        comodel_name = 'res.partner',
        string = 'Cliente',
        store = True,
    )