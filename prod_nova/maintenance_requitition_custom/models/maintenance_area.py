# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError


class MaintenanceArea(models.Model):
    _name = 'maintenance.area'

    name = fields.Char(

    string='Nombre',
    store = True,

    )

    user_ids = fields.Many2many(
        'res.users', 'maintenance_area_users_rel', string="Usuarios"
    )
