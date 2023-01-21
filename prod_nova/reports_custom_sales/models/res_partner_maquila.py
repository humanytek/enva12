# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError


class PartnerMaquila(models.Model):
    _name = 'partner.maquila'
    _description = "Partner Maquila"

    name = fields.Many2one(
        comodel_name = 'res.partner',
        string = 'Cliente',
        store = True,
    )

class PartnerMaquilaLamina(models.Model):
    _name = 'partner.maquila.lamina'
    _description = "Partner Maquila Lamina"
    
    name = fields.Many2one(
        comodel_name = 'res.partner',
        string = 'Cliente',
        store = True,
    )
