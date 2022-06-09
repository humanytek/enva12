# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError


class BudgetGoal(models.Model):
    _name = 'budget.goal.receipts'
    _description = "Budget Goal Receipts"

    name = fields.Many2one(
        comodel_name = 'res.partner',
        string = 'Cliente',
        store = True,
    )


    date_from=fields.Date(
        string='Fecha Inicial',
        required=True,
        store=True,
    )

    date_to=fields.Date(
        string='Fecha Final',
        required=True,
        store=True,
    )


    goal=fields.Float(
        string='Meta x Mes',
        store=True,
    )

    note = fields.Char(
        string='Comentarios',
        store=True,
    )
