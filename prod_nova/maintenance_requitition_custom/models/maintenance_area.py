# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError


class MaintenanceArea(models.Model):
    _name = 'maintenance.area'
    _description = "Maintenance Area"

    name = fields.Char(

    string='Nombre',
    store = True,

    )

    user_ids = fields.Many2many(
        comodel_name='res.users',
        string="Usuarios",
        store=True,
    )
