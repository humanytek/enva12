# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

NAME_STATE_INCOME=[
  ('VENTA DE CARTÓN','VENTA DE CARTÓN'),
  ('VENTA DE PAPEL','VENTA DE PAPEL'),
  ('VENTA DE DESPERDICIO','VENTA DE DESPERDICIO'),
  ('OTRAS VENTAS CARTON','OTRAS VENTAS CARTON'),
  ('OTRAS VENTAS PAPEL','OTRAS VENTAS PAPEL'),
  ('DESCUENTOS Y DEVOLUCIONES SOBRE VENTAS','DESCUENTOS Y DEVOLUCIONES SOBRE VENTAS'),
  ('MATERIA PRIMA PAPEL','MATERIA PRIMA PAPEL'),
  ('GASTOS DE FABRICACIÓN FIJOS PAPEL','GASTOS DE FABRICACIÓN FIJOS PAPEL'),
  ('GASTOS DE FABRICACIÓN VARIABLES PAPEL','GASTOS DE FABRICACIÓN VARIABLES PAPEL'),
  ('MATERIA PRIMA CARTÓN','MATERIA PRIMA CARTÓN'),
  ('GASTOS DE FABRICACIÓN FIJOS CARTÓN','GASTOS DE FABRICACIÓN FIJOS CARTÓN'),
  ('GASTOS DE FABRICACIÓN VARIABLES CARTÓN','GASTOS DE FABRICACIÓN VARIABLES CARTÓN'),
  ('GASTOS DE ADMINISTRACIÓN','GASTOS DE ADMINISTRACIÓN'),
  ('GASTOS DE VENTAS','GASTOS DE VENTAS')
]

class BudgetStatementIncome(models.Model):
    _name = 'budget.statement.income'


    # name = fields.Selection(
    #     NAME_STATE_INCOME,
    #     'Nombre Estado de resultados',
    #     required=True,
    #     store=True,
    # )

    name = fields.Many2one(
        comodel_name = 'budget.nova',
        string = 'Nombre Presupuesto',
        store = True

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

    amount_per_month=fields.Float(
    string='Monto mes',
    store=True,
    )
