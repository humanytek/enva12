# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

NAME_TYPE_REPORTS=[
('BALANCE GENERAL','BALANCE GENERAL'),
('ESTADO DE RESULTADOS','ESTADO DE RESULTADOS')
]
NAME_VOLUMEN_SALE=[
('TONELADAS FACTURADAS CAJAS','TONELADAS FACTURADAS CAJAS'),
('TONELADAS FACTURADAS PAPEL','TONELADAS FACTURADAS PAPEL')
]
NAME_TYPE_REPORTS_BALANCE=[
('RESULTADO EJ. ANT','RESULTADO EJ. ANT'),
('RESULTADO DEL EJERCICIO','RESULTADO DEL EJERCICIO')
]
class ReportsGroup(models.Model):
    _name = 'reports.group'
    _description = "Reports Group"


    name = fields.Char(
        'Titulo',
        required = True,
        store = True,
    )

    code = fields.Char(
        string = 'codigo',
        required =True,
        store = True
    )

    title = fields.Boolean(
    string='Es Titulo?'
    )

    acum_invisible = fields.Boolean(
    string='Invisible?'
    )

    has_a_group = fields.Boolean(
    string = 'Grupo de Cuenta?',
    store=True,
    )

    group_id = fields.Many2one(
        comodel_name = 'account.group',
        string = 'Group',
        store = True

    )

    order = fields.Integer(
    string = 'Order',
    store = True
    )

    level = fields.Integer(
    string = 'Level',
    store = True
    )

    type = fields.Selection(
    NAME_TYPE_REPORTS,
    string = 'Tipo de reporte',
    required=True,
    store=True,
    )

    type_balance=fields.Selection(
    NAME_TYPE_REPORTS_BALANCE,
    string = 'Calculo Especial Balance',
    store=True,
    )

    titulo_porcent = fields.Boolean(
    string = 'Titulo con Porcentaje?',
    store=True,
    )

    has_a_budget = fields.Boolean(
    string = 'Tiene Presupuesto?',
    store=True,
    )

    budget_nova_id = fields.Many2one(
        comodel_name = 'budget.nova',
        string = 'Nombre Presupuesto',
        store = True

    )

    caculate_especial_cventa = fields.Boolean(
        string = 'Calculo Especial Costo de Venta',
        store = True,
    )

    costo_venta_id = fields.Many2one(
        comodel_name = 'list.cost.sale.nova',
        string = 'Costo de Venta',
        store = True

    )

    formula = fields.Boolean(
    string = 'Es Formula?',
    store=True,
    )

    formula_porcent = fields.Boolean(
    string = 'Incluir porcentaje?',
    store=True,
    )

    expresion = fields.Char(
    string = "Formula",
    store=True,
    )

    expresion_porcent = fields.Char(
    string = "Calcular Porcentaje",
    store=True,
    )

    color_red = fields.Boolean(
    string = "Color Rojo",
    store=True,
    )

    negative = fields.Boolean(
    string = "Negativo",
    store=True,
    )

    volumen = fields.Boolean(
    string = 'Mostrar Volumen de Ventas?',
    store=True,
    )

    volumen_ventas = fields.Selection(
        NAME_VOLUMEN_SALE,
        string = 'Volumen de Ventas',
        store = True
        )
