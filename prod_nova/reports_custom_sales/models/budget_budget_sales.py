# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError


class BudgetBudgetSales(models.Model):
    _name = 'budget.budget.sales'
    _description = "Budget Budget Sales"

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

    price_unit_per_month=fields.Float(
        string='Precio por mes',
        store=True,
    )
