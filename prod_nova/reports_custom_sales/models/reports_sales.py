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


class ReportsSales(models.AbstractModel):
    _name = "report.sales.nova"
    _description = "Reports Sales"
    _inherit = 'account.report'

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    # filter_all_entries = False

    def _get_columns_name(self, options):
        return [
        {'name': ''},
        {'name': _('ESTIMADO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('FACTURACION'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('TEORICO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('AVANCE TONS'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('DESV.TONS'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('TEND.TONS FIN DE MES'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PROYECTADO VENTAS'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('% CUBRIMIENTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('COMENTARIOS'), 'style': 'text-align: left;white-space:nowrap;'},
        {'name': _('PRECIO x KG ESTIMADO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO x KG REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('DESV.PRECIO X KG'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRESUPUESTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('MES ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PROM.AÑO ANTERIOR TONS'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('MES AÑO ANTERIOR TONS'), 'class': 'number', 'style': 'white-space:nowrap;'},
        ]



    def _invoice_line_partner(self,options,line_id,partner_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        sql_query ="""
            SELECT
                    rp.name as cliente,
                    SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal,
                    SUM(pt.weight*aml.quantity) as total_weight
                    FROM account_move_line aml
                    LEFT JOIN product_product pp ON pp.id=aml.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_move am ON am.id=aml.move_id
                    LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                    WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice'
                    AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                    AND aml.partner_id="""+partner_id+"""
                    AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                    AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                    AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                    AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                    AND aml.exclude_from_invoice_tab=False
                    GROUP BY rp.name
                    ORDER BY rp.name ASC
        """


        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchone()
        if result==None:
            result=('',0,0)

        return result

    def _invoice_line_partner_n(self,options,line_id,partner_id,date_f,date_t):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        sql_query ="""
            SELECT
                    rp.name as cliente,
                    SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal,
                    SUM(pt.weight*aml.quantity) as total_weight
                    FROM account_move_line aml
                    LEFT JOIN product_product pp ON pp.id=aml.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_move am ON am.id=aml.move_id
                    LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                    WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice'
                    AND aml.partner_id="""+partner_id+""" AND am.date_applied >= '"""+date_f+"""' AND am.date_applied <= '"""+date_t+"""'
                    AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                    AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                    AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                    AND aml.exclude_from_invoice_tab=False
                    GROUP BY rp.name
                    ORDER BY rp.name ASC
        """


        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchone()
        if result==None:
            result=('',0,0)

        return result

    def _invoice_line_partner_ant_month(self,options,line_id,partner_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=-1)
        dt=fields.Date.from_string(date_from)+timedelta(days=-1)
        sql_query ="""
            SELECT
                    rp.name as cliente,
                    SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal,
                    SUM(pt.weight*aml.quantity) as total_weight
                    FROM account_move_line aml
                    LEFT JOIN product_product pp ON pp.id=aml.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_move am ON am.id=aml.move_id
                    LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                    WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice'
                    AND (am.not_accumulate=False OR am.not_accumulate is NULL ) AND aml.partner_id="""+partner_id+""" AND am.date_applied >= '"""+str(df)+"""'
                    AND am.date_applied <= '"""+str(dt)+"""'
                    AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                    AND pt.name not ilike 'ANTICIPO DE CLIENTE%'
                    AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                    AND aml.exclude_from_invoice_tab=False
                    GROUP BY rp.name
                    ORDER BY rp.name ASC
        """


        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchone()
        if result==None:
            result=('',0,0)

        return result


    def daterange(self,date1, date2):
        for n in range(int ((fields.Date.from_string(date2) - fields.Date.from_string(date1)).days)+1):
            yield fields.Date.from_string(date1) + timedelta(n)


    def _billed_days(self,options,line_id):
        contador=0
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']

        for dt in self.daterange(date_from, date_to):
            if dt.weekday() < 5:
                contador+=1

        return contador


    def _partner_trend(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        clientes={}
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            (SELECT
                rp.name as cliente,rp.id
                FROM account_move_line aml
                LEFT JOIN product_product pp ON pp.id=aml.product_id
                LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                LEFT JOIN account_move am ON am.id=aml.move_id
                LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice'
                AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                AND rp.id not in (SELECT pm.name FROM partner_maquila pm)
                AND rp.id not in (SELECT pml.name FROM partner_maquila_lamina pml)
                AND aml.exclude_from_invoice_tab=False
                GROUP BY rp.name,rp.id
                )
                UNION
                (SELECT
                    rp.name as cliente,rp.id
                    FROM trend_budget_sales tbs
                    LEFT JOIN res_partner rp ON rp.id=tbs.name
                    WHERE tbs.date_from >= '"""+date_from+"""' AND tbs.date_to <= '"""+str(df)+"""'
                    AND rp.id not in (SELECT pm.name FROM partner_maquila pm)
                    AND rp.id not in (SELECT pml.name FROM partner_maquila_lamina pml)
                    GROUP BY rp.name,rp.id
                )
                    UNION
                (SELECT
                    rp.name as cliente,rp.id
                    FROM budget_budget_sales bbs
                    LEFT JOIN res_partner rp ON rp.id=bbs.name
                    WHERE bbs.date_from >= '"""+date_from+"""' AND bbs.date_to <= '"""+str(df)+"""'
                    AND rp.id not in (SELECT pm.name FROM partner_maquila pm)
                    AND rp.id not in (SELECT pml.name FROM partner_maquila_lamina pml)
                    GROUP BY rp.name,rp.id
                )
                ORDER BY cliente




        """
        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        results = self.env.cr.fetchall()

        for r in results:
            presupuesto=self._get_budget_sales(r[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
            if presupuesto:
                clientes[r[1]]=(r[0],presupuesto)
            else:
                clientes[r[1]]=(r[0],0)



        # if result==None:
        #     result=(0,)

        return clientes

    def _partner_trendArchi(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        clientes={}
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""
            (SELECT
                rp.name as cliente,rp.id
                FROM account_move_line aml
                LEFT JOIN product_product pp ON pp.id=aml.product_id
                LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                LEFT JOIN account_move am ON am.id=aml.move_id
                LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                AND rp.id in (SELECT pm.name FROM partner_maquila pm)
                AND aml.exclude_from_invoice_tab=False
                GROUP BY rp.name,rp.id
                )
                UNION
                (SELECT
                    rp.name as cliente,rp.id
                    FROM trend_budget_sales tbs
                    LEFT JOIN res_partner rp ON rp.id=tbs.name
                    WHERE tbs.date_from >= '"""+date_from+"""' AND tbs.date_to <= '"""+str(df)+"""'
                    AND rp.id in (SELECT pm.name FROM partner_maquila pm)
                    GROUP BY rp.name,rp.id
                )
                    UNION
                (SELECT
                    rp.name as cliente,rp.id
                    FROM budget_budget_sales bbs
                    LEFT JOIN res_partner rp ON rp.id=bbs.name
                    WHERE bbs.date_from >= '"""+date_from+"""' AND bbs.date_to <= '"""+str(df)+"""'
                    AND rp.id in (SELECT pm.name FROM partner_maquila pm)
                    GROUP BY rp.name,rp.id
                )
                ORDER BY cliente
        """
        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        results = self.env.cr.fetchall()

        for r in results:
            presupuesto=self._get_budget_sales(r[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
            if presupuesto:
                clientes[r[1]]=(r[0],presupuesto)
            else:
                clientes[r[1]]=(r[0],0)

        # if result==None:
        #     result=(0,)

        return clientes

    def _partner_trendLamina(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        clientes={}
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""
            (SELECT
                rp.name as cliente,rp.id
                FROM account_move_line aml
                LEFT JOIN product_product pp ON pp.id=aml.product_id
                LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                LEFT JOIN account_move am ON am.id=aml.move_id
                LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice'
                AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                AND rp.id in (SELECT pml.name FROM partner_maquila_lamina pml)
                AND aml.exclude_from_invoice_tab=False
                GROUP BY rp.name,rp.id
                )
                UNION
                (SELECT
                    rp.name as cliente,rp.id
                    FROM trend_budget_sales tbs
                    LEFT JOIN res_partner rp ON rp.id=tbs.name
                    WHERE tbs.date_from >= '"""+date_from+"""' AND tbs.date_to <= '"""+str(df)+"""'
                    AND rp.id in (SELECT pml.name FROM partner_maquila_lamina pml)
                    GROUP BY rp.name,rp.id
                )
                    UNION
                (SELECT
                    rp.name as cliente,rp.id
                    FROM budget_budget_sales bbs
                    LEFT JOIN res_partner rp ON rp.id=bbs.name
                    WHERE bbs.date_from >= '"""+date_from+"""' AND bbs.date_to <= '"""+str(df)+"""'
                    AND rp.id in (SELECT pml.name FROM partner_maquila_lamina pml)
                    GROUP BY rp.name,rp.id
                )
                ORDER BY cliente
        """
        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        results = self.env.cr.fetchall()

        for r in results:
            presupuesto=self._get_budget_sales(r[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
            if presupuesto:
                clientes[r[1]]=(r[0],presupuesto)
            else:
                clientes[r[1]]=(r[0],0)

        # if result==None:
        #     result=(0,)

        return clientes

    def _get_budget_sales(self, nstate, date_f,date_t):
        budget=self.env['trend.budget.sales'].search(['&','&',('name','=',nstate),('date_from','>=',date_f),('date_to','<=',date_t)])

        budgetacum=0
        if budget:
            for b in budget:
                budgetacum+=b.kg_per_month

        return budgetacum

    def _get_budget_budget_sales(self, nstate, date_f,date_t):
        budget=self.env['budget.budget.sales'].search(['&','&',('name','=',nstate),('date_from','>=',date_f),('date_to','<=',date_t)])

        budgetacum=0
        if budget:
            for b in budget:
                budgetacum+=b.kg_per_month

        return budgetacum

    def _get_project_user_sales(self, nstate, date_f,date_t):
        budget=self.env['project.user.sales'].search(['&','&',('name','=',nstate),('date_from','>=',date_f),('date_to','<=',date_t)])

        budgetacum=0
        if budget:
            for b in budget:
                budgetacum+=b.kg_per_month

        return budgetacum

    def _get_budget_sales_price(self, nstate, date_f,date_t):
        budget=self.env['trend.budget.sales'].search(['&','&',('name','=',nstate),('date_from','>=',date_f),('date_to','<=',date_t)])
        contador=0
        budgetacum=0
        contador=len(budget)
        if budget:
            for b in budget:
                budgetacum+=b.price_unit_per_month
        if contador!=0:
            budgetacum=budgetacum/contador
        else:
            budgetacum=budgetacum

        return budgetacum


    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)
        first_day_previous_fy = self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'] + relativedelta(years=-1)
        last_day_previous_fy = self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'] + timedelta(days=-1)
        invoices = self._partner_trend(options,line_id)
        invoicesarchi = self._partner_trendArchi(options,line_id)
        invoiceslamina = self._partner_trendLamina(options,line_id)

        # invoices=self.env['account.invoice'].search([('type','in',['out_invoice']),('state','in',['open','in_payment','paid']),('date_applied','>=',date_from),('date_applied','<=',date_to)],order='partner_id ASC,date_applied')
        lines.append({
        'id': 'cliente',
        'name': 'CLIENTE',
        'level': 0,
        'class': 'cliente',
        'columns':[
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},

        ],
        })

        if invoices:
            contadorinv=0

            estimado=0
            presupuesto=0
            facturacion=0
            facturacion_mes_ant=0
            porcentcubrimiento=0
            teorico=0
            tprice_per_kgp=0
            tprice_per_kgf=0
            tavancetons=0
            tdesvton=0
            tdesvpricekg=0
            ttendtonsfm=0
            tpromprevyear=0
            tmesprevyear=0
            tprojectventas=0
            desv_price_per_kg=0
            contadorinv=len(invoices)
            for invoice,value in sorted(invoices.items(), key=lambda x:x[1][1], reverse= True)  :
                budget=self._get_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                budget_budget=self._get_budget_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                project_sale=self._get_project_user_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                comentarios = self.env['project.user.sales'].search(['&','&',('name','=',invoice),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))])
                invoices_line=self._invoice_line_partner(options,line_id,str(invoice))
                invoices_line_ant_month=self._invoice_line_partner_ant_month(options,line_id,str(invoice))
                invoices_line_promedio=self._invoice_line_partner_n(options,line_id,str(invoice), str(first_day_previous_fy),str(last_day_previous_fy))
                invoices_line_lymonth=self._invoice_line_partner_n(options,line_id,str(invoice),str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))
                price_per_kg=self._get_budget_sales_price(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
                if price_per_kg and price_per_kg>0:
                    if invoices_line[1]>0:
                        if invoices_line[2]>0:
                             desv_price_per_kg=((invoices_line[1]/invoices_line[2])-price_per_kg)/price_per_kg
                            # desv_price_per_kg=price_per_kg/(invoices_line[1]/invoices_line[2])-1

                        else:
                            desv_price_per_kg=0
                    else:
                        desv_price_per_kg=0
                else:
                    desv_price_per_kg=0


                if project_sale and project_sale!=0:
                    if budget!=0 and budget!=False:
                        porcentcubrimiento=(project_sale/1000)/(budget/1000)
                    else:
                        porcentcubrimiento=0
                else:
                    if invoices_line[2]!=0 and (self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0) and (bussines_days.bussines_days!=0 or bussines_days!=False) and (budget!=False or budget!=0) :
                        porcentcubrimiento=(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days)/(budget/1000)
                    else:
                        porcentcubrimiento=0


                lines.append({
                        'id': str(value[0]),
                        'name': str(value[0]),
                        'level': 2,
                        'class': 'activo',
                        'columns':[
                            {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line[2]/1000))},
                            {'name':"{:,}".format(0) if budget==0 or bussines_days.bussines_days==0 or self._billed_days(options,line_id)==0 else "{:,}".format(round(((budget/1000)/bussines_days.bussines_days)*self._billed_days(options,line_id)))},
                            {'name':"{:.0%}".format(0) if budget==0 else "{:.0%}".format((invoices_line[2]/1000)/(budget/1000))},
                            {'name':"{:.0%}".format(0) if budget==0 or invoices_line[2]==0 or bussines_days.bussines_days==0 or self._billed_days(options,line_id)==0 else "{:.0%}".format(((invoices_line[2]/1000)/(((budget/1000)/bussines_days.bussines_days)*self._billed_days(options,line_id))-1))},
                            {'name':0 if self._billed_days(options,line_id)==0 or budget==False else "{:,}".format(round(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days))},
                            {'name':(0 if self._billed_days(options,line_id)==0 or budget==False else "{:,}".format(round(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days))) if project_sale==False else "{:,}".format(round(project_sale/1000)) },
                            {'name': "{:.0%}".format(porcentcubrimiento)},
                            {'name':'' if comentarios.note==False else comentarios.note, 'style': 'text-align: left;white-space:nowrap;'},
                            {'name':0 if price_per_kg==False else self.format_value(price_per_kg) },
                            {'name':0 if invoices_line[2]==0 else self.format_value(invoices_line[1]/invoices_line[2])},
                            {'name':"{:.0%}".format(desv_price_per_kg) },
                            {'name':0 if budget_budget==False else "{:,}".format(round(budget_budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line_ant_month[2]/1000))},
                            {'name':0 if invoices_line_promedio[2]==0 else "{:,}".format(round((invoices_line_promedio[2]/12)/1000)) },
                            {'name':"{:,}".format(round((invoices_line_lymonth[2])/1000)) },

                        ],
                        })

                estimado+=budget/1000
                presupuesto+=budget_budget/1000
                facturacion+=invoices_line[2]/1000
                facturacion_mes_ant+=invoices_line_ant_month[2]/1000
                if price_per_kg!=False:
                    tprice_per_kgp+=price_per_kg/contadorinv
                else:
                    tprice_per_kgp+=0
                if invoices_line[1] !=0 or invoices_line[2]!=0:
                    tprice_per_kgf+=(invoices_line[1]/invoices_line[2])/contadorinv
                else:
                    tprice_per_kgf+=0
                tpromprevyear+=(invoices_line_promedio[2]/12)/1000
                tmesprevyear+=invoices_line_lymonth[2]/1000
                if project_sale:
                    tprojectventas+=project_sale/1000
                else:
                    if self._billed_days(options,line_id)!=0:
                        tprojectventas+=((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days
                    else:
                        tprojectventas+=0

            if estimado!=0:
                tavancetons=facturacion/estimado
            else:
                tavancetons=0

            if bussines_days.bussines_days!=0:
                if (estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)!=0:
                    tdesvton=(facturacion/((estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)))-1
                else:
                    tdesvton=0

            else:
                tdesvton=0

            if tprice_per_kgp!=0:
                tdesvpricekg=(tprice_per_kgf-tprice_per_kgp)/tprice_per_kgp
            else:
                tdesvpricekg=0
            if self._billed_days(options,line_id)!=0:
                ttendtonsfm=(facturacion/self._billed_days(options,line_id))*bussines_days.bussines_days
            else:
                ttendtonsfm=0
            if estimado!=0 or bussines_days.bussines_days!=0 or self._billed_days(options,line_id)!=0:
                teorico=(estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)
            else:
                teorico=0





            lines.append({
                    'id': 'total',
                    'name': 'TOTAL',
                    'level': 0,
                    'class': 'total',
                    'columns':[
                    {'name': "{:,}".format(round(estimado))},
                    {'name': "{:,}".format(round(facturacion))},
                    {'name': "{:,}".format(round(teorico))},
                    {'name':"{:.0%}".format(tavancetons)},
                    {'name':"{:.0%}".format(tdesvton)},
                    {'name':"{:,}".format(round(ttendtonsfm))},
                    {'name':"{:,}".format(round(tprojectventas))},
                    {'name': "{:.0%}".format(tprojectventas/estimado) if (tprojectventas!=0 and estimado!=0) else "{:.0%}".format(0)},
                    {'name':''},
                    {'name': self.format_value(tprice_per_kgp)},
                    {'name':self.format_value(tprice_per_kgf)},
                    {'name':"{:.0%}".format(tdesvpricekg)},
                    {'name': "{:,}".format(round(presupuesto))},
                    {'name': "{:,}".format(round(facturacion_mes_ant))},
                    {'name':"{:,}".format(round(tpromprevyear))},
                    {'name':"{:,}".format(round(tmesprevyear))},
                    ],
                    })

        if invoicesarchi:
            contadorinv=0

            estimado=0
            presupuesto=0
            facturacion=0
            facturacion_mes_ant=0
            porcentcubrimiento=0
            teorico=0
            tprice_per_kgp=0
            tprice_per_kgf=0
            tavancetons=0
            tdesvton=0
            tdesvpricekg=0
            ttendtonsfm=0
            tpromprevyear=0
            tmesprevyear=0
            tprojectventas=0
            desv_price_per_kg=0
            contadorinv=len(invoicesarchi)
            lines.append({
            'id': 'cliente',
            'name': 'CLIENTE',
            'level': 0,
            'class': 'cliente',
            'columns':[
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},

            ],
            })

            for invoice,value in sorted(invoicesarchi.items(), key=lambda x:x[1][1], reverse= True) :
                budget=self._get_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                budget_budget=self._get_budget_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                project_sale=self._get_project_user_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                comentarios = self.env['project.user.sales'].search(['&','&',('name','=',invoice),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))])
                invoices_line=self._invoice_line_partner(options,line_id,str(invoice))
                invoices_line_ant_month=self._invoice_line_partner_ant_month(options,line_id,str(invoice))
                invoices_line_promedio=self._invoice_line_partner_n(options,line_id,str(invoice), str(first_day_previous_fy),str(last_day_previous_fy))
                invoices_line_lymonth=self._invoice_line_partner_n(options,line_id,str(invoice),str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))
                price_per_kg=self._get_budget_sales_price(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
                if price_per_kg and price_per_kg>0:
                    if invoices_line[1]>0:
                        if invoices_line[2]>0:
                             desv_price_per_kg=((invoices_line[1]/invoices_line[2])-price_per_kg)/price_per_kg
                            # desv_price_per_kg=price_per_kg/(invoices_line[1]/invoices_line[2])-1

                        else:
                            desv_price_per_kg=0
                    else:
                        desv_price_per_kg=0
                else:
                    desv_price_per_kg=0

                if project_sale and project_sale!=0:
                    if budget!=0 and budget!=False:
                        porcentcubrimiento=(project_sale/1000)/(budget/1000)
                    else:
                        porcentcubrimiento=0
                else:
                    if invoices_line[2]!=0 and (self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0) and (bussines_days.bussines_days!=0 or bussines_days!=False) and (budget!=False or budget!=0) :
                        porcentcubrimiento=(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days)/(budget/1000)
                    else:
                        porcentcubrimiento=0

                lines.append({
                        'id': str(value[0]),
                        'name': str(value[0]),
                        'level': 2,
                        'class': 'activo',
                        'columns':[
                            {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line[2]/1000))},
                            {'name':"{:,}".format(0) if budget==0 or bussines_days.bussines_days==0 or self._billed_days(options,line_id)==0 else "{:,}".format(round(((budget/1000)/bussines_days.bussines_days)*self._billed_days(options,line_id)))},
                            {'name':"{:.0%}".format(0) if budget==0 else "{:.0%}".format((invoices_line[2]/1000)/(budget/1000))},
                            {'name':"{:.0%}".format(0) if budget==0 or invoices_line[2]==0 or bussines_days.bussines_days==0 or self._billed_days(options,line_id)==0 else "{:.0%}".format(((invoices_line[2]/1000)/(((budget/1000)/bussines_days.bussines_days)*self._billed_days(options,line_id))-1))},
                            {'name':0 if self._billed_days(options,line_id)==0 or budget==False else "{:,}".format(round(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days))},
                            {'name':(0 if self._billed_days(options,line_id)==0 or budget==False else "{:,}".format(round(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days))) if project_sale==False else "{:,}".format(round(project_sale/1000)) },
                            {'name': "{:.0%}".format(porcentcubrimiento)},
                            {'name':'' if comentarios.note==False else comentarios.note},
                            {'name':0 if price_per_kg==False else self.format_value(price_per_kg) },
                            {'name':0 if invoices_line[2]==0 else self.format_value(invoices_line[1]/invoices_line[2])},
                            {'name':"{:.0%}".format(desv_price_per_kg) },
                            {'name':0 if budget_budget==False else "{:,}".format(round(budget_budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line_ant_month[2]/1000))},
                            {'name':0 if invoices_line_promedio[2]==0 else "{:,}".format(round((invoices_line_promedio[2]/12)/1000)) },
                            {'name':"{:,}".format(round((invoices_line_lymonth[2])/1000)) },

                        ],
                        })

                estimado+=budget/1000
                presupuesto+=budget_budget/1000
                facturacion+=invoices_line[2]/1000
                facturacion_mes_ant+=invoices_line_ant_month[2]/1000
                if price_per_kg!=False:
                    tprice_per_kgp+=price_per_kg/contadorinv
                else:
                    tprice_per_kgp+=0
                if invoices_line[2]!=0 or invoices_line[1]!=0:
                    tprice_per_kgf+=(invoices_line[1]/invoices_line[2])/contadorinv
                else:
                    tprice_per_kgf+=0
                tpromprevyear+=(invoices_line_promedio[2]/12)/1000
                tmesprevyear+=invoices_line_lymonth[2]/1000
                if project_sale:
                    tprojectventas+=project_sale/1000
                else:
                    if self._billed_days(options,line_id)!=0:
                        tprojectventas+=((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days
                    else:
                        tprojectventas+=0

            if estimado!=0:
                tavancetons=facturacion/estimado
            else:
                tavancetons=0

            if bussines_days.bussines_days!=0:
                if (estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)!=0:
                    tdesvton=(facturacion/((estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)))-1
                else:
                    tdesvton=0

            else:
                tdesvton=0

            if tprice_per_kgp!=0:
                tdesvpricekg=(tprice_per_kgf-tprice_per_kgp)/tprice_per_kgp
            else:
                tdesvpricekg=0
            if self._billed_days(options,line_id)!=0:
                ttendtonsfm=(facturacion/self._billed_days(options,line_id))*bussines_days.bussines_days
            else:
                ttendtonsfm=0
            if estimado!=0 or bussines_days.bussines_days!=0 or self._billed_days(options,line_id)!=0:
                teorico=(estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)
            else:
                teorico=0



            lines.append({
                    'id': 'total',
                    'name': 'TOTAL',
                    'level': 0,
                    'class': 'total',
                    'columns':[
                    {'name': "{:,}".format(round(estimado))},
                    {'name': "{:,}".format(round(facturacion))},
                    {'name': "{:,}".format(round(teorico))},
                    {'name':"{:.0%}".format(tavancetons)},
                    {'name':"{:.0%}".format(tdesvton)},
                    {'name':"{:,}".format(round(ttendtonsfm))},
                    {'name':"{:,}".format(round(tprojectventas))},
                    {'name': "{:.0%}".format(tprojectventas/estimado) if (tprojectventas!=0 and estimado!=0) else "{:.0%}".format(0)},
                    {'name':''},
                    {'name': self.format_value(tprice_per_kgp)},
                    {'name':self.format_value(tprice_per_kgf)},
                    {'name':"{:.0%}".format(tdesvpricekg)},
                    {'name': "{:,}".format(round(presupuesto))},
                    {'name': "{:,}".format(round(facturacion_mes_ant))},
                    {'name':"{:,}".format(round(tpromprevyear))},
                    {'name':"{:,}".format(round(tmesprevyear))},
                    ],
                    })
        if invoiceslamina:
            contadorinv=0

            estimado=0
            presupuesto=0
            facturacion=0
            facturacion_mes_ant=0
            porcentcubrimiento=0
            teorico=0
            tprice_per_kgp=0
            tprice_per_kgf=0
            tavancetons=0
            tdesvton=0
            tdesvpricekg=0
            ttendtonsfm=0
            tpromprevyear=0
            tmesprevyear=0
            tprojectventas=0
            desv_price_per_kg=0
            contadorinv=len(invoiceslamina)
            lines.append({
            'id': 'cliente',
            'name': 'CLIENTE',
            'level': 0,
            'class': 'cliente',
            'columns':[
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},
                    {'name':''},

            ],
            })

            for invoice,value in sorted(invoiceslamina.items(), key=lambda x:x[1][1], reverse= True) :
                budget=self._get_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                budget_budget=self._get_budget_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                project_sale=self._get_project_user_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                comentarios = self.env['project.user.sales'].search(['&','&',('name','=',invoice),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))])
                invoices_line=self._invoice_line_partner(options,line_id,str(invoice))
                invoices_line_ant_month=self._invoice_line_partner_ant_month(options,line_id,str(invoice))
                invoices_line_promedio=self._invoice_line_partner_n(options,line_id,str(invoice), str(first_day_previous_fy),str(last_day_previous_fy))
                invoices_line_lymonth=self._invoice_line_partner_n(options,line_id,str(invoice),str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))
                price_per_kg=self._get_budget_sales_price(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
                if price_per_kg and price_per_kg>0:
                    if invoices_line[1]>0:
                        if invoices_line[2]>0:
                             desv_price_per_kg=((invoices_line[1]/invoices_line[2])-price_per_kg)/price_per_kg
                            # desv_price_per_kg=price_per_kg/(invoices_line[1]/invoices_line[2])-1

                        else:
                            desv_price_per_kg=0
                    else:
                        desv_price_per_kg=0
                else:
                    desv_price_per_kg=0

                if project_sale and project_sale!=0:
                    if budget!=0 and budget!=False:
                        porcentcubrimiento=(project_sale/1000)/(budget/1000)
                    else:
                        porcentcubrimiento=0
                else:
                    if invoices_line[2]!=0 and (self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0) and (bussines_days.bussines_days!=0 or bussines_days!=False) and (budget!=False or budget!=0) :
                        porcentcubrimiento=(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days)/(budget/1000)
                    else:
                        porcentcubrimiento=0

                lines.append({
                        'id': str(value[0]),
                        'name': str(value[0]),
                        'level': 2,
                        'class': 'activo',
                        'columns':[
                            {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line[2]/1000))},
                            {'name':"{:,}".format(0) if budget==0 or bussines_days.bussines_days==0 or self._billed_days(options,line_id)==0 else "{:,}".format(round(((budget/1000)/bussines_days.bussines_days)*self._billed_days(options,line_id)))},
                            {'name':"{:.0%}".format(0) if budget==0 else "{:.0%}".format((invoices_line[2]/1000)/(budget/1000))},
                            {'name':"{:.0%}".format(0) if budget==0 or invoices_line[2]==0 or bussines_days.bussines_days==0 or self._billed_days(options,line_id)==0 else "{:.0%}".format(((invoices_line[2]/1000)/(((budget/1000)/bussines_days.bussines_days)*self._billed_days(options,line_id))-1))},
                            {'name':0 if self._billed_days(options,line_id)==0 or budget==False else "{:,}".format(round(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days))},
                            {'name':(0 if self._billed_days(options,line_id)==0 or budget==False else "{:,}".format(round(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days))) if project_sale==False else "{:,}".format(round(project_sale/1000)) },
                            {'name': "{:.0%}".format(porcentcubrimiento)},
                            {'name':'' if comentarios.note==False else comentarios.note},
                            {'name':0 if price_per_kg==False else self.format_value(price_per_kg) },
                            {'name':0 if invoices_line[2]==0 else self.format_value(invoices_line[1]/invoices_line[2])},
                            {'name':"{:.0%}".format(desv_price_per_kg) },
                            {'name':0 if budget_budget==False else "{:,}".format(round(budget_budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line_ant_month[2]/1000))},
                            {'name':0 if invoices_line_promedio[2]==0 else "{:,}".format(round((invoices_line_promedio[2]/12)/1000)) },
                            {'name':"{:,}".format(round((invoices_line_lymonth[2])/1000)) },

                        ],
                        })

                estimado+=budget/1000
                presupuesto+=budget_budget/1000
                facturacion+=invoices_line[2]/1000
                facturacion_mes_ant+=invoices_line_ant_month[2]/1000
                if price_per_kg!=False:
                    tprice_per_kgp+=price_per_kg/contadorinv
                else:
                    tprice_per_kgp+=0
                if invoices_line[2]!=0 or invoices_line[1]!=0:
                    tprice_per_kgf+=(invoices_line[1]/invoices_line[2])/contadorinv
                else:
                    tprice_per_kgf+=0
                tpromprevyear+=(invoices_line_promedio[2]/12)/1000
                tmesprevyear+=invoices_line_lymonth[2]/1000
                if project_sale:
                    tprojectventas+=project_sale/1000
                else:
                    if self._billed_days(options,line_id)!=0:
                        tprojectventas+=((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days
                    else:
                        tprojectventas+=0

            if estimado!=0:
                tavancetons=facturacion/estimado
            else:
                tavancetons=0

            if bussines_days.bussines_days!=0:
                if (estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)!=0:
                    tdesvton=(facturacion/((estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)))-1
                else:
                    tdesvton=0

            else:
                tdesvton=0

            if tprice_per_kgp!=0:
                tdesvpricekg=(tprice_per_kgf-tprice_per_kgp)/tprice_per_kgp
            else:
                tdesvpricekg=0
            if self._billed_days(options,line_id)!=0:
                ttendtonsfm=(facturacion/self._billed_days(options,line_id))*bussines_days.bussines_days
            else:
                ttendtonsfm=0
            if estimado!=0 or bussines_days.bussines_days!=0 or self._billed_days(options,line_id)!=0:
                teorico=(estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)
            else:
                teorico=0



            lines.append({
                    'id': 'total',
                    'name': 'TOTAL',
                    'level': 0,
                    'class': 'total',
                    'columns':[
                    {'name': "{:,}".format(round(estimado))},
                    {'name': "{:,}".format(round(facturacion))},
                    {'name': "{:,}".format(round(teorico))},
                    {'name':"{:.0%}".format(tavancetons)},
                    {'name':"{:.0%}".format(tdesvton)},
                    {'name':"{:,}".format(round(ttendtonsfm))},
                    {'name':"{:,}".format(round(tprojectventas))},
                    {'name': "{:.0%}".format(tprojectventas/estimado) if (tprojectventas!=0 and estimado!=0) else "{:.0%}".format(0)},
                    {'name':''},
                    {'name': self.format_value(tprice_per_kgp)},
                    {'name':self.format_value(tprice_per_kgf)},
                    {'name':"{:.0%}".format(tdesvpricekg)},
                    {'name': "{:,}".format(round(presupuesto))},
                    {'name': "{:,}".format(round(facturacion_mes_ant))},
                    {'name':"{:,}".format(round(tpromprevyear))},
                    {'name':"{:,}".format(round(tmesprevyear))},
                    ],
                    })


        return lines

    @api.model
    def _get_report_name(self):
        return _('Tendencia de Ventas')
