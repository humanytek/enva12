# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

class BudgetNova(models.Model):
    _name = 'budget.nova'
    _description = "Budget Nova"
    
    name = fields.Char(
        'Nombre Presupuesto Nova',
        required = True,
        store = True,
    )
