# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError


class ProjectUserSales(models.Model):
    _name = 'project.user.sales'
    _description = "Project User Sales"

    name = fields.Many2one(
        comodel_name = 'res.partner',
        string = 'Cliente',
        store = True,
    )


    date_from=fields.Date(
        string='Date From',
        required=True,
        store=True,
    )

    date_to=fields.Date(
        string='Date To',
        required=True,
        store=True,
    )

    kg_per_month=fields.Float(
        string='Kilogramos por mes',
        store=True,
    )

    note = fields.Char(
        string='Comentarios',
        store=True,
    )
