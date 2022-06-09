# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

NAME_COST_SALE = [
    ('MATERIA PRIMA PAPEL', 'MATERIA PRIMA PAPEL'),
    ('GASTOS DE FABRICACIÓN FIJOS PAPEL', 'GASTOS DE FABRICACIÓN FIJOS PAPEL'),
    ('GASTOS DE FABRICACIÓN VARIABLES PAPEL', 'GASTOS DE FABRICACIÓN VARIABLES PAPEL'),
    ('MATERIA PRIMA CARTÓN', 'MATERIA PRIMA CARTÓN'),
    ('GASTOS DE FABRICACIÓN FIJOS CARTÓN', 'GASTOS DE FABRICACIÓN FIJOS CARTÓN'),
    ('GASTOS DE FABRICACIÓN VARIABLES CARTÓN', 'GASTOS DE FABRICACIÓN VARIABLES CARTÓN'),
]


class PorcentCostSale(models.Model):
    _name = 'porcent.cost.sale'
    _description = "Porcent Cost Sale"


    name = fields.Many2one(
        comodel_name = 'list.cost.sale.nova',
        string = 'Nombre Costo de Venta',
        required=True,
        store = True
    )

    porcent= fields.Float(
        store=True,
        string='Porcent',
        required=True,
    )

    group_finantial_id = fields.Many2one(
        comodel_name = 'account.group.nova',
        string = 'Group',
        store = True,
        required=True,
        default =False,
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

    cost_per_month=fields.Float(
    compute='_cost_month',
    string='Costo por mes',

    )

    porcent_per_month=fields.Float(
    compute='_porcent_cost_month',
    string='Porcentaje por mes',

    )



    def _post_account(self,group,date_from,date_to):

        sql_query ="""
            SELECT COALESCE(sum(aml.debit),0) as debit,
                COALESCE(sum(aml.credit),0) as credit,COALESCE(sum(aml.balance),0) as balance
                FROM account_move_line aml
                LEFT JOIN account_account aa on aa.id=aml.account_id
                WHERE aa.group_finantial_id = %s AND aml.date >= %s AND aml.date <= %s
                GROUP BY aa.group_finantial_id
        """
        params =[group,date_from,date_to]
        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,0,0)
        # results = self.env.cr.dictfetchall()
        return result


    @api.depends('date_from','date_to','cost_per_month','group_finantial_id')
    def _cost_month(self):
        for cm in self:
            if cm.group_finantial_id:
                if cm.date_from and cm.date_to:
                    cost_month=self._post_account(cm.group_finantial_id.id,cm.date_from,cm.date_to)
                    cm.cost_per_month=cost_month[2]



    @api.depends('cost_per_month','porcent_per_month','porcent')
    def _porcent_cost_month(self):
        for pcm in self:
            pcm.porcent_per_month=(pcm.cost_per_month*pcm.porcent)/100
