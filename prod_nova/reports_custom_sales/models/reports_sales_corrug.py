# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import time
from odoo import api, models,fields, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.addons.web.controllers.main import clean_action
_logger = logging.getLogger(__name__)


class ReportsSalesCorrug(models.AbstractModel):
    _name = "reports.sales.corrug.nova"
    _description = "Reports Sales Corrug"
    _inherit = 'account.report'

    filter_date = {'mode': 'range', 'filter': 'this_month'}


    def _get_columns_name(self, options):
        name_month={
        1:'ENERO',
        2:'FEBRERO',
        3:'MARZO',
        4:'ABRIL',
        5:'MAYO',
        6:'JUNIO',
        7:'JULIO',
        8:'AGOSTO',
        9:'SEPTIEMBRE',
        10:'OCTUBRE',
        11:'NOVIEMBRE',
        12:'DICIEMBRE',
        }

        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df5=fields.Date.from_string(date_from)+relativedelta(months=1)
        df3=fields.Date.from_string(date_from)+relativedelta(months=-3)
        df2=fields.Date.from_string(date_from)+relativedelta(months=-2)
        df1=fields.Date.from_string(date_from)+relativedelta(months=-1)
        df=fields.Date.from_string(date_from)
        return [
        {'name': ''},
        {'name': _('PRODUCTO'), 'class': 'number', 'style':'text-align: left; white-space:nowrap;'},
        {'name': name_month.get(df3.month, "NA"), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name':''},
        {'name':name_month.get(df2.month, "NA"), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': ''},
        {'name': name_month.get(df1.month, "NA"), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': ''},
        {'name': name_month.get(df.month, "NA"), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': ''},
        {'name': _('PROM DIARIO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': name_month.get(df5.month, "NA"), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('TENDENCIA')+str(' ')+name_month.get(df5.month, "NA"), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('ADICIONALES'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('ODOO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        ]

    def _partner_line(self,options,line_id):
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=-3)
        sql_query ="""
            SELECT
                    aml.partner_id as id_cliente,
                    rp.name as cliente,
                    SUM(pt.weight*aml.quantity) as total_weight
                    FROM account_move_line aml
                    LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                    LEFT JOIN product_product pp ON pp.id=aml.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_move am ON am.id=aml.move_id
                    WHERE am.state!='draft' AND am.state!='cancel'
                    AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                    AND rp.id not in (SELECT pm.name FROM partner_maquila pm)
                    AND rp.id not in (SELECT pml.name FROM partner_maquila_lamina pml)
                    AND am.move_type='out_invoice' AND am.date_applied >= '"""+str(df)+"""' AND am.date_applied <= '"""+date_to+"""'
                    AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                    AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                    AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                    AND aml.exclude_from_invoice_tab=False
                    GROUP BY rp.name,aml.partner_id
                    ORDER BY rp.name ASC

        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _partner_line_maquila(self,options,line_id):
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=-3)
        sql_query ="""
            SELECT
                    aml.partner_id as id_cliente,
                    rp.name as cliente,
                    SUM(pt.weight*aml.quantity) as total_weight
                    FROM account_move_line aml
                    LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                    LEFT JOIN product_product pp ON pp.id=aml.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_move am ON am.id=aml.move_id
                    WHERE am.state!='draft' AND am.state!='cancel'
                    AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                    AND rp.id in (SELECT pm.name FROM partner_maquila pm)
                    AND am.move_type='out_invoice' AND am.date_applied >= '"""+str(df)+"""' AND am.date_applied <= '"""+date_to+"""'
                    AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                    AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                    AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                    AND aml.exclude_from_invoice_tab=False
                    GROUP BY rp.name,aml.partner_id
                    ORDER BY rp.name ASC

        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _partner_line_lamina(self,options,line_id):
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=-3)
        sql_query ="""
            SELECT
                    aml.partner_id as id_cliente,
                    rp.name as cliente,
                    SUM(pt.weight*aml.quantity) as total_weight
                    FROM account_move_line aml
                    LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                    LEFT JOIN product_product pp ON pp.id=aml.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_move am ON am.id=aml.move_id
                    WHERE am.state!='draft' AND am.state!='cancel'
                    AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                    AND rp.id in (SELECT pml.name FROM partner_maquila_lamina pml)
                    AND am.move_type='out_invoice' AND am.date_applied >= '"""+str(df)+"""' AND am.date_applied <= '"""+date_to+"""'
                    AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                    AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                    AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                    AND aml.exclude_from_invoice_tab=False
                    GROUP BY rp.name,aml.partner_id
                    ORDER BY rp.name ASC

        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _partner_weight_line(self,options,line_id,partner_id,date_from,date_to):

        sql_query ="""
            SELECT
                    aml.partner_id as id_cliente,
                    rp.name as cliente,
                    COALESCE(SUM(pt.weight*aml.quantity),0) as total_weight
                    FROM account_move_line aml
                    LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                    LEFT JOIN product_product pp ON pp.id=aml.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_move am ON am.id=aml.move_id
                    WHERE am.state!='draft' AND am.state!='cancel'
                    AND aml.partner_id = """+partner_id+"""
                    AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                    AND am.move_type='out_invoice' AND am.date_applied >= '"""+str(date_from)+"""' AND am.date_applied <= '"""+str(date_to)+"""'
                    AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                    AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                    AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                    AND aml.exclude_from_invoice_tab=False
                    GROUP BY rp.name,aml.partner_id
                    ORDER BY rp.name ASC

        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _product_line(self,options,line_id,partner_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=-3)

        sql_query ="""

                SELECT
                        pp.default_code as codep,
                        pt.name as producto,
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel'
                        AND aml.partner_id = """+partner_id+"""
                        AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND am.move_type='out_invoice' AND am.date_applied >= '"""+str(df)+"""'
                        AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                        AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                        AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND aml.exclude_from_invoice_tab=False
                        GROUP BY pp.default_code,pt.name
                        ORDER BY pp.default_code ASC

            """


        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _weight_line(self,options,line_id,partner_id,product_code,date_from,date_to):

        sql_query ="""

                SELECT

                        COALESCE(SUM(pt.weight*aml.quantity),0) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel'
                        AND aml.partner_id = """+partner_id+"""
                        AND pp.default_code = '"""+str(product_code)+"""'
                        AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND am.move_type='out_invoice' AND am.date_applied >= '"""+str(date_from)+"""'
                        AND am.date_applied <= '"""+str(date_to)+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                        AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                        AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND aml.exclude_from_invoice_tab=False
                        GROUP BY pp.default_code,pt.name
                        ORDER BY pp.default_code ASC

            """


        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _get_budget_sales(self, nstate, date_f,date_t):
        budget=self.env['trend.budget.sales'].search(['&','&',('name','=',nstate),('date_from','>=',date_f),('date_to','<=',date_t)])

        budgetacum=0
        if budget:
            for b in budget:
                budgetacum+=b.kg_per_month

        return budgetacum

    def _get_budget_sales_add(self, nstate, date_f,date_t):
        budget=self.env['trend.budget.sales'].search(['&','&',('name','=',nstate),('date_from','>=',date_f),('date_to','<=',date_t)])

        budgetacum=0
        if budget:
            for b in budget:
                budgetacum+=b.kg_per_month_add

        return budgetacum


    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        clientes= self._partner_line(options,line_id)
        clientes_maquila= self._partner_line_maquila(options,line_id)
        clientes_lamina= self._partner_line_lamina(options,line_id)
        df3=fields.Date.from_string(date_from)+relativedelta(months=-3)
        df2=fields.Date.from_string(date_from)+relativedelta(months=-2)
        df1=fields.Date.from_string(date_from)+relativedelta(months=-1)
        df5=fields.Date.from_string(date_from)+relativedelta(months=1)
        df=fields.Date.from_string(date_from)
        bussines_days5=self.env['bussines.days'].search([('name','=',str(df5.month)),('year','=',str(df5.year))])
        bussines_days3=self.env['bussines.days'].search([('name','=',str(df3.month)),('year','=',str(df3.year))])
        bussines_days2=self.env['bussines.days'].search([('name','=',str(df2.month)),('year','=',str(df2.year))])
        bussines_days1=self.env['bussines.days'].search([('name','=',str(df1.month)),('year','=',str(df1.year))])
        bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
        if clientes:
            lines.append({
            'id': 'NOVA',
            'name': 'EMPAQUESNOVA' ,
            'level': 0,
            'class': 'cliente',
            'columns':[
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
            ],
            })
            stwm3=0
            stwmp3=0
            stwm2=0
            stwmp2=0
            stwm1=0
            stwmp1=0
            stwm=0
            stwmp=0
            stwpd=0
            stwm5=0
            stbudget=0
            stbudgetadd=0
            stodoo=0
            for c in clientes:
                totalc_weight_prom=0
                budget=self._get_budget_sales(c['id_cliente'], fields.Date.from_string(date_from)+relativedelta(months=1),fields.Date.from_string(date_from)+relativedelta(months=2)+timedelta(days=-1))
                budget_add=self._get_budget_sales_add(c['id_cliente'], fields.Date.from_string(date_from)+relativedelta(months=1),fields.Date.from_string(date_from)+relativedelta(months=2)+timedelta(days=-1))
                totalc_weight_month_3=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from)+relativedelta(months=-3),fields.Date.from_string(date_from)+relativedelta(months=-2)+timedelta(days=-1))
                totalc_weight_month_2=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from)+relativedelta(months=-2),fields.Date.from_string(date_from)+relativedelta(months=-1)+timedelta(days=-1))
                totalc_weight_month_1=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1))
                totalc_weight=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                if totalc_weight_month_3 and bussines_days3:
                    totalc_weight_prom+=((totalc_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)
                else:
                    totalc_weight_prom+=0

                if totalc_weight_month_2 and bussines_days2:
                    totalc_weight_prom+=((totalc_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)
                else:
                    totalc_weight_prom+=0
                if totalc_weight_month_1 and bussines_days1:
                    totalc_weight_prom+=((totalc_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)
                else:
                    totalc_weight_prom+=0
                if totalc_weight and bussines_days:
                    totalc_weight_prom+=((totalc_weight[0]['total_weight']/1000)/bussines_days.bussines_days)
                else:
                    totalc_weight_prom+=0


                lines.append({
                'id': c['id_cliente'],
                'name': str(c['cliente'][0:48]) ,
                'level': 1,
                'class': 'cliente',
                'columns':[
                        {'name':""},
                        {'name':"{:,}".format(round(totalc_weight_month_3[0]['total_weight']/1000)) if totalc_weight_month_3 else 0 },
                        {'name':"{:,}".format(round((totalc_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)) if totalc_weight_month_3 and bussines_days3 else 0},
                        {'name':"{:,}".format(round(totalc_weight_month_2[0]['total_weight']/1000)) if totalc_weight_month_2 else 0 },
                        {'name':"{:,}".format(round((totalc_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)) if totalc_weight_month_2 and bussines_days2 else 0 },
                        {'name':"{:,}".format(round(totalc_weight_month_1[0]['total_weight']/1000)) if totalc_weight_month_1 else 0 },
                        {'name':"{:,}".format(round((totalc_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)) if totalc_weight_month_1 and bussines_days1 else 0 },
                        {'name':"{:,}".format(round(totalc_weight[0]['total_weight']/1000)) if totalc_weight else 0 },
                        {'name':"{:,}".format(round((totalc_weight[0]['total_weight']/1000)/bussines_days.bussines_days)) if totalc_weight and bussines_days else 0 },
                        {'name':"{:.2f}".format(totalc_weight_prom/4) },
                        {'name':"{:.2f}".format((totalc_weight_prom/4)*bussines_days5.bussines_days) },
                        {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                        {'name':0 if budget_add==False else "{:,}".format(round(budget_add/1000)) },
                        {'name':0 if budget_add==False and budget==False else "{:,}".format(round((budget+budget_add)/1000)) },
                ],
                })

                if totalc_weight_month_3:
                    stwm3+=totalc_weight_month_3[0]['total_weight']/1000
                else:
                    stwm3+=0

                if totalc_weight_month_3 and bussines_days3:
                    stwmp3+=(totalc_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days
                else:
                    stwmp3+=0

                if totalc_weight_month_2:
                    stwm2+=totalc_weight_month_2[0]['total_weight']/1000
                else:
                    stwm2+=0

                if totalc_weight_month_2 and bussines_days2:
                    stwmp2+=(totalc_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days
                else:
                    stwmp2+=0

                if totalc_weight_month_1:
                    stwm1+=totalc_weight_month_1[0]['total_weight']/1000
                else:
                    stwm1+=0

                if totalc_weight_month_1 and bussines_days1:
                    stwmp1+=(totalc_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days
                else:
                    stwmp1+=0

                if totalc_weight:
                    stwm+=totalc_weight[0]['total_weight']/1000
                else:
                    stwm+=0
                if totalc_weight and bussines_days:
                    stwmp+=(totalc_weight[0]['total_weight']/1000)/bussines_days.bussines_days
                else:
                    stwmp+=0

                stwpd+=totalc_weight_prom/4
                stwm5+=(totalc_weight_prom/4)*bussines_days5.bussines_days
                if budget==False:
                    stbudget+=0
                else:
                    stbudget+=budget/1000

                if budget_add==False:
                    stbudgetadd+=0
                else:
                    stbudgetadd+=budget_add/1000
                if budget_add==False and budget==False:

                    stodoo+=0
                else:
                    stodoo+=(budget+budget_add)/1000

                productos=self._product_line(options,line_id,str(c['id_cliente']))
                if productos:
                    for p in productos:
                        total_weight_prom=0
                        total_weight_month_3=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from)+relativedelta(months=-3),fields.Date.from_string(date_from)+relativedelta(months=-2)+timedelta(days=-1))
                        total_weight_month_2=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from)+relativedelta(months=-2),fields.Date.from_string(date_from)+relativedelta(months=-1)+timedelta(days=-1))
                        total_weight_month_1=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1))
                        total_weight=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                        if total_weight_month_3 and bussines_days3:
                            total_weight_prom+=((total_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)
                        else:
                            total_weight_prom+=0

                        if total_weight_month_2 and bussines_days2:
                            total_weight_prom+=((total_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)
                        else:
                            total_weight_prom+=0
                        if total_weight_month_1 and bussines_days1:
                            total_weight_prom+=((total_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)
                        else:
                            total_weight_prom+=0
                        if total_weight and bussines_days:
                            total_weight_prom+=((total_weight[0]['total_weight']/1000)/bussines_days.bussines_days)
                        else:
                            total_weight_prom+=0

                        lines.append({
                        'id': 'producto',
                        'name': str(p['codep']) ,
                        'level': 2,
                        'class': 'producto',
                        'columns':[
                                {'name':str(p['producto'][0:100])},
                                {'name':"{:,}".format(round(total_weight_month_3[0]['total_weight']/1000)) if total_weight_month_3 else 0 },
                                {'name':"{:,}".format(round((total_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)) if total_weight_month_3 and bussines_days3 else 0},
                                {'name':"{:,}".format(round(total_weight_month_2[0]['total_weight']/1000)) if total_weight_month_2 else 0 },
                                {'name':"{:,}".format(round((total_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)) if total_weight_month_2 and bussines_days2 else 0},
                                {'name':"{:,}".format(round(total_weight_month_1[0]['total_weight']/1000)) if total_weight_month_1 else 0 },
                                {'name':"{:,}".format(round((total_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)) if total_weight_month_1 and bussines_days1 else 0 },
                                {'name':"{:,}".format(round(total_weight[0]['total_weight']/1000)) if total_weight else 0 },
                                {'name':"{:,}".format(round((total_weight[0]['total_weight']/1000)/bussines_days.bussines_days)) if total_weight and bussines_days else 0 },
                                {'name':"{:.2f}".format(total_weight_prom/4) },
                                {'name':"{:.2f}".format((total_weight_prom/4)*bussines_days5.bussines_days) },
                                {'name':""},
                                {'name':""},
                                {'name':""},
                        ],
                        })
            lines.append({
            'id': 'TNOVA',
            'name': 'TOTAL EMPAQUESNOVA' ,
            'level': 0,
            'class': 'total',
            'columns':[
                    {'name':""},
                    {'name':"{:,}".format(round(stwm3))},
                    {'name':"{:,}".format(round(stwmp3))},
                    {'name':"{:,}".format(round(stwm2))},
                    {'name':"{:,}".format(round(stwmp2))},
                    {'name':"{:,}".format(round(stwm1))},
                    {'name':"{:,}".format(round(stwmp1))},
                    {'name':"{:,}".format(round(stwm))},
                    {'name':"{:,}".format(round(stwmp))},
                    {'name':"{:.2f}".format(stwpd)},
                    {'name':"{:.2f}".format(stwm5)},
                    {'name':"{:,}".format(round(stbudget))},
                    {'name':"{:,}".format(round(stbudgetadd))},
                    {'name':"{:,}".format(round(stodoo))},
            ],
            })
        if clientes_maquila:
            lines.append({
            'id': 'MAQUILA',
            'name': 'MAQUILA ARCHIMEX' ,
            'level': 0,
            'class': 'cliente',
            'columns':[
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
            ],
            })
            stwm3=0
            stwmp3=0
            stwm2=0
            stwmp2=0
            stwm1=0
            stwmp1=0
            stwm=0
            stwmp=0
            stwpd=0
            stwm5=0
            stbudget=0
            stbudgetadd=0
            stodoo=0
            for c in clientes_maquila:
                totalc_weight_prom=0
                budget=self._get_budget_sales(c['id_cliente'], fields.Date.from_string(date_from)+relativedelta(months=1),fields.Date.from_string(date_from)+relativedelta(months=2)+timedelta(days=-1))
                budget_add=self._get_budget_sales_add(c['id_cliente'], fields.Date.from_string(date_from)+relativedelta(months=1),fields.Date.from_string(date_from)+relativedelta(months=2)+timedelta(days=-1))
                totalc_weight_month_3=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from)+relativedelta(months=-3),fields.Date.from_string(date_from)+relativedelta(months=-2)+timedelta(days=-1))
                totalc_weight_month_2=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from)+relativedelta(months=-2),fields.Date.from_string(date_from)+relativedelta(months=-1)+timedelta(days=-1))
                totalc_weight_month_1=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1))
                totalc_weight=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                if totalc_weight_month_3 and bussines_days3:
                    totalc_weight_prom+=((totalc_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)
                else:
                    totalc_weight_prom+=0

                if totalc_weight_month_2 and bussines_days2:
                    totalc_weight_prom+=((totalc_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)
                else:
                    totalc_weight_prom+=0
                if totalc_weight_month_1 and bussines_days1:
                    totalc_weight_prom+=((totalc_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)
                else:
                    totalc_weight_prom+=0
                if totalc_weight and bussines_days:
                    totalc_weight_prom+=((totalc_weight[0]['total_weight']/1000)/bussines_days.bussines_days)
                else:
                    totalc_weight_prom+=0

                lines.append({
                'id': c['id_cliente'],
                'name': str(c['cliente'][0:48]) ,
                'level': 1,
                'class': 'cliente',
                'columns':[
                        {'name':""},
                        {'name':"{:,}".format(round(totalc_weight_month_3[0]['total_weight']/1000)) if totalc_weight_month_3 else 0 },
                        {'name':"{:,}".format(round((totalc_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)) if totalc_weight_month_3 and bussines_days3 else 0},
                        {'name':"{:,}".format(round(totalc_weight_month_2[0]['total_weight']/1000)) if totalc_weight_month_2 else 0 },
                        {'name':"{:,}".format(round((totalc_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)) if totalc_weight_month_2 and bussines_days2 else 0 },
                        {'name':"{:,}".format(round(totalc_weight_month_1[0]['total_weight']/1000)) if totalc_weight_month_1 else 0 },
                        {'name':"{:,}".format(round((totalc_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)) if totalc_weight_month_1 and bussines_days1 else 0 },
                        {'name':"{:,}".format(round(totalc_weight[0]['total_weight']/1000)) if totalc_weight else 0 },
                        {'name':"{:,}".format(round((totalc_weight[0]['total_weight']/1000)/bussines_days.bussines_days)) if totalc_weight and bussines_days else 0 },
                        {'name':"{:.2f}".format(totalc_weight_prom/4) },
                        {'name':"{:.2f}".format((totalc_weight_prom/4)*bussines_days5.bussines_days) },
                        {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                        {'name':0 if budget_add==False else "{:,}".format(round(budget_add/1000)) },
                        {'name':0 if budget_add==False and budget==False else "{:,}".format(round((budget+budget_add)/1000)) },
                ],
                })

                if totalc_weight_month_3:
                    stwm3+=totalc_weight_month_3[0]['total_weight']/1000
                else:
                    stwm3+=0

                if totalc_weight_month_3 and bussines_days3:
                    stwmp3+=(totalc_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days
                else:
                    stwmp3+=0

                if totalc_weight_month_2:
                    stwm2+=totalc_weight_month_2[0]['total_weight']/1000
                else:
                    stwm2+=0

                if totalc_weight_month_2 and bussines_days2:
                    stwmp2+=(totalc_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days
                else:
                    stwmp2+=0

                if totalc_weight_month_1:
                    stwm1+=totalc_weight_month_1[0]['total_weight']/1000
                else:
                    stwm1+=0

                if totalc_weight_month_1 and bussines_days1:
                    stwmp1+=(totalc_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days
                else:
                    stwmp1+=0

                if totalc_weight:
                    stwm+=totalc_weight[0]['total_weight']/1000
                else:
                    stwm+=0
                if totalc_weight and bussines_days:
                    stwmp+=(totalc_weight[0]['total_weight']/1000)/bussines_days.bussines_days
                else:
                    stwmp+=0

                stwpd+=totalc_weight_prom/4
                stwm5+=(totalc_weight_prom/4)*bussines_days5.bussines_days
                if budget==False:
                    stbudget+=0
                else:
                    stbudget+=budget/1000

                if budget_add==False:
                    stbudgetadd+=0
                else:
                    stbudgetadd+=budget_add/1000
                if budget_add==False and budget==False:

                    stodoo+=0
                else:
                    stodoo+=(budget+budget_add)/1000

                productos=self._product_line(options,line_id,str(c['id_cliente']))
                if productos:
                    for p in productos:
                        total_weight_prom=0
                        total_weight_month_3=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from)+relativedelta(months=-3),fields.Date.from_string(date_from)+relativedelta(months=-2)+timedelta(days=-1))
                        total_weight_month_2=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from)+relativedelta(months=-2),fields.Date.from_string(date_from)+relativedelta(months=-1)+timedelta(days=-1))
                        total_weight_month_1=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1))
                        total_weight=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                        if total_weight_month_3 and bussines_days3:
                            total_weight_prom+=((total_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)
                        else:
                            total_weight_prom+=0

                        if total_weight_month_2 and bussines_days2:
                            total_weight_prom+=((total_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)
                        else:
                            total_weight_prom+=0
                        if total_weight_month_1 and bussines_days1:
                            total_weight_prom+=((total_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)
                        else:
                            total_weight_prom+=0
                        if total_weight and bussines_days:
                            total_weight_prom+=((total_weight[0]['total_weight']/1000)/bussines_days.bussines_days)
                        else:
                            total_weight_prom+=0

                        lines.append({
                        'id': 'producto',
                        'name': str(p['codep']) ,
                        'level': 2,
                        'class': 'producto',
                        'columns':[
                                {'name':str(p['producto'][0:100])},
                                {'name':"{:,}".format(round(total_weight_month_3[0]['total_weight']/1000)) if total_weight_month_3 else 0 },
                                {'name':"{:,}".format(round((total_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)) if total_weight_month_3 and bussines_days3 else 0},
                                {'name':"{:,}".format(round(total_weight_month_2[0]['total_weight']/1000)) if total_weight_month_2 else 0 },
                                {'name':"{:,}".format(round((total_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)) if total_weight_month_2 and bussines_days2 else 0},
                                {'name':"{:,}".format(round(total_weight_month_1[0]['total_weight']/1000)) if total_weight_month_1 else 0 },
                                {'name':"{:,}".format(round((total_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)) if total_weight_month_1 and bussines_days1 else 0 },
                                {'name':"{:,}".format(round(total_weight[0]['total_weight']/1000)) if total_weight else 0 },
                                {'name':"{:,}".format(round((total_weight[0]['total_weight']/1000)/bussines_days.bussines_days)) if total_weight and bussines_days else 0 },
                                {'name':"{:.2f}".format(total_weight_prom/4) },
                                {'name':"{:.2f}".format((total_weight_prom/4)*bussines_days5.bussines_days) },
                                {'name':""},
                                {'name':""},
                                {'name':""},
                        ],
                        })

            lines.append({
            'id': 'TMAQUILA',
            'name': 'TOTAL MAQUILA ARCHIMEX' ,
            'level': 0,
            'class': 'total',
            'columns':[
                    {'name':""},
                    {'name':"{:,}".format(round(stwm3))},
                    {'name':"{:,}".format(round(stwmp3))},
                    {'name':"{:,}".format(round(stwm2))},
                    {'name':"{:,}".format(round(stwmp2))},
                    {'name':"{:,}".format(round(stwm1))},
                    {'name':"{:,}".format(round(stwmp1))},
                    {'name':"{:,}".format(round(stwm))},
                    {'name':"{:,}".format(round(stwmp))},
                    {'name':"{:.2f}".format(stwpd)},
                    {'name':"{:.2f}".format(stwm5)},
                    {'name':"{:,}".format(round(stbudget))},
                    {'name':"{:,}".format(round(stbudgetadd))},
                    {'name':"{:,}".format(round(stodoo))},
            ],
            })
        if clientes_lamina:
            lines.append({
            'id': 'LAMINA',
            'name': 'LAMINA' ,
            'level': 0,
            'class': 'cliente',
            'columns':[
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
                    {'name':""},
            ],
            })
            stwm3=0
            stwmp3=0
            stwm2=0
            stwmp2=0
            stwm1=0
            stwmp1=0
            stwm=0
            stwmp=0
            stwpd=0
            stwm5=0
            stbudget=0
            stbudgetadd=0
            stodoo=0
            for c in clientes_lamina:
                totalc_weight_prom=0
                budget=self._get_budget_sales(c['id_cliente'], fields.Date.from_string(date_from)+relativedelta(months=1),fields.Date.from_string(date_from)+relativedelta(months=2)+timedelta(days=-1))
                budget_add=self._get_budget_sales_add(c['id_cliente'], fields.Date.from_string(date_from)+relativedelta(months=1),fields.Date.from_string(date_from)+relativedelta(months=2)+timedelta(days=-1))
                totalc_weight_month_3=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from)+relativedelta(months=-3),fields.Date.from_string(date_from)+relativedelta(months=-2)+timedelta(days=-1))
                totalc_weight_month_2=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from)+relativedelta(months=-2),fields.Date.from_string(date_from)+relativedelta(months=-1)+timedelta(days=-1))
                totalc_weight_month_1=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1))
                totalc_weight=self._partner_weight_line(options,line_id,str(c['id_cliente']),fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                if totalc_weight_month_3 and bussines_days3:
                    totalc_weight_prom+=((totalc_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)
                else:
                    totalc_weight_prom+=0

                if totalc_weight_month_2 and bussines_days2:
                    totalc_weight_prom+=((totalc_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)
                else:
                    totalc_weight_prom+=0
                if totalc_weight_month_1 and bussines_days1:
                    totalc_weight_prom+=((totalc_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)
                else:
                    totalc_weight_prom+=0
                if totalc_weight and bussines_days:
                    totalc_weight_prom+=((totalc_weight[0]['total_weight']/1000)/bussines_days.bussines_days)
                else:
                    totalc_weight_prom+=0

                lines.append({
                'id': c['id_cliente'],
                'name': str(c['cliente'][0:48]) ,
                'level': 1,
                'class': 'cliente',
                'columns':[
                        {'name':""},
                        {'name':"{:,}".format(round(totalc_weight_month_3[0]['total_weight']/1000)) if totalc_weight_month_3 else 0 },
                        {'name':"{:,}".format(round((totalc_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)) if totalc_weight_month_3 and bussines_days3 else 0},
                        {'name':"{:,}".format(round(totalc_weight_month_2[0]['total_weight']/1000)) if totalc_weight_month_2 else 0 },
                        {'name':"{:,}".format(round((totalc_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)) if totalc_weight_month_2 and bussines_days2 else 0 },
                        {'name':"{:,}".format(round(totalc_weight_month_1[0]['total_weight']/1000)) if totalc_weight_month_1 else 0 },
                        {'name':"{:,}".format(round((totalc_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)) if totalc_weight_month_1 and bussines_days1 else 0 },
                        {'name':"{:,}".format(round(totalc_weight[0]['total_weight']/1000)) if totalc_weight else 0 },
                        {'name':"{:,}".format(round((totalc_weight[0]['total_weight']/1000)/bussines_days.bussines_days)) if totalc_weight and bussines_days else 0 },
                        {'name':"{:.2f}".format(totalc_weight_prom/4) },
                        {'name':"{:.2f}".format((totalc_weight_prom/4)*bussines_days5.bussines_days) },
                        {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                        {'name':0 if budget_add==False else "{:,}".format(round(budget_add/1000)) },
                        {'name':0 if budget_add==False and budget==False else "{:,}".format(round((budget+budget_add)/1000)) },
                ],
                })

                if totalc_weight_month_3:
                    stwm3+=totalc_weight_month_3[0]['total_weight']/1000
                else:
                    stwm3+=0

                if totalc_weight_month_3 and bussines_days3:
                    stwmp3+=(totalc_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days
                else:
                    stwmp3+=0

                if totalc_weight_month_2:
                    stwm2+=totalc_weight_month_2[0]['total_weight']/1000
                else:
                    stwm2+=0

                if totalc_weight_month_2 and bussines_days2:
                    stwmp2+=(totalc_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days
                else:
                    stwmp2+=0

                if totalc_weight_month_1:
                    stwm1+=totalc_weight_month_1[0]['total_weight']/1000
                else:
                    stwm1+=0

                if totalc_weight_month_1 and bussines_days1:
                    stwmp1+=(totalc_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days
                else:
                    stwmp1+=0

                if totalc_weight:
                    stwm+=totalc_weight[0]['total_weight']/1000
                else:
                    stwm+=0
                if totalc_weight and bussines_days:
                    stwmp+=(totalc_weight[0]['total_weight']/1000)/bussines_days.bussines_days
                else:
                    stwmp+=0

                stwpd+=totalc_weight_prom/4
                stwm5+=(totalc_weight_prom/4)*bussines_days5.bussines_days
                if budget==False:
                    stbudget+=0
                else:
                    stbudget+=budget/1000

                if budget_add==False:
                    stbudgetadd+=0
                else:
                    stbudgetadd+=budget_add/1000
                if budget_add==False and budget==False:

                    stodoo+=0
                else:
                    stodoo+=(budget+budget_add)/1000

                productos=self._product_line(options,line_id,str(c['id_cliente']))
                if productos:
                    for p in productos:
                        total_weight_prom=0
                        total_weight_month_3=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from)+relativedelta(months=-3),fields.Date.from_string(date_from)+relativedelta(months=-2)+timedelta(days=-1))
                        total_weight_month_2=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from)+relativedelta(months=-2),fields.Date.from_string(date_from)+relativedelta(months=-1)+timedelta(days=-1))
                        total_weight_month_1=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1))
                        total_weight=self._weight_line(options,line_id,str(c['id_cliente']),str(p['codep']),fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                        if total_weight_month_3 and bussines_days3:
                            total_weight_prom+=((total_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)
                        else:
                            total_weight_prom+=0

                        if total_weight_month_2 and bussines_days2:
                            total_weight_prom+=((total_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)
                        else:
                            total_weight_prom+=0
                        if total_weight_month_1 and bussines_days1:
                            total_weight_prom+=((total_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)
                        else:
                            total_weight_prom+=0
                        if total_weight and bussines_days:
                            total_weight_prom+=((total_weight[0]['total_weight']/1000)/bussines_days.bussines_days)
                        else:
                            total_weight_prom+=0

                        lines.append({
                        'id': 'producto',
                        'name': str(p['codep']) ,
                        'level': 2,
                        'class': 'producto',
                        'columns':[
                                {'name':str(p['producto'][0:100])},
                                {'name':"{:,}".format(round(total_weight_month_3[0]['total_weight']/1000)) if total_weight_month_3 else 0 },
                                {'name':"{:,}".format(round((total_weight_month_3[0]['total_weight']/1000)/bussines_days3.bussines_days)) if total_weight_month_3 and bussines_days3 else 0},
                                {'name':"{:,}".format(round(total_weight_month_2[0]['total_weight']/1000)) if total_weight_month_2 else 0 },
                                {'name':"{:,}".format(round((total_weight_month_2[0]['total_weight']/1000)/bussines_days2.bussines_days)) if total_weight_month_2 and bussines_days2 else 0},
                                {'name':"{:,}".format(round(total_weight_month_1[0]['total_weight']/1000)) if total_weight_month_1 else 0 },
                                {'name':"{:,}".format(round((total_weight_month_1[0]['total_weight']/1000)/bussines_days1.bussines_days)) if total_weight_month_1 and bussines_days1 else 0 },
                                {'name':"{:,}".format(round(total_weight[0]['total_weight']/1000)) if total_weight else 0 },
                                {'name':"{:,}".format(round((total_weight[0]['total_weight']/1000)/bussines_days.bussines_days)) if total_weight and bussines_days else 0 },
                                {'name':"{:.2f}".format(total_weight_prom/4) },
                                {'name':"{:.2f}".format((total_weight_prom/4)*bussines_days5.bussines_days) },
                                {'name':""},
                                {'name':""},
                                {'name':""},
                        ],
                        })

            lines.append({
            'id': 'TLAMINA',
            'name': 'TOTAL LAMINA' ,
            'level': 0,
            'class': 'total',
            'columns':[
                    {'name':""},
                    {'name':"{:,}".format(round(stwm3))},
                    {'name':"{:,}".format(round(stwmp3))},
                    {'name':"{:,}".format(round(stwm2))},
                    {'name':"{:,}".format(round(stwmp2))},
                    {'name':"{:,}".format(round(stwm1))},
                    {'name':"{:,}".format(round(stwmp1))},
                    {'name':"{:,}".format(round(stwm))},
                    {'name':"{:,}".format(round(stwmp))},
                    {'name':"{:.2f}".format(stwpd)},
                    {'name':"{:.2f}".format(stwm5)},
                    {'name':"{:,}".format(round(stbudget))},
                    {'name':"{:,}".format(round(stbudgetadd))},
                    {'name':"{:,}".format(round(stodoo))},
            ],
            })
        return lines

    @api.model
    def _get_report_name(self):
        return _('ESTIMACION DE VENTAS CORRUGADO')
