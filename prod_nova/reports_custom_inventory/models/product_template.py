# -*- coding: utf-8 -*-

from odoo import api, fields, models,_


class ProductTemplateNova(models.Model):
    _inherit = 'product.template'

    partner_cus_id= fields.Many2one(
        'res.partner',
        string = 'Cliente',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )