# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class Res_Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    stock_whp = fields.Boolean(
    string='Permitir Existencia en almacen?',
    store=True,
    )