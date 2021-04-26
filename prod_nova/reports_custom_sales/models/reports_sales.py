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

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    # filter_all_entries = False

    def _get_columns_name(self, options):
        return [
        {'name': ''},
        {'name': _('ESTIMADO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('FACTURACION'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('AVANCE TONS'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('DESV.TONS'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('TEND.TONS FIN DE MES'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PROYECTADO VENTAS'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('COMENTARIOS'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO x KG ESTIMADO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO x KG REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('DESV.PRECIO X KG'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRESUPUESTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
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
                    SUM(ail.quantity*(ail.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=ai.date_applied AND rcr.currency_id=ai.currency_id AND rcr.company_id=ai.company_id)))) as subtotal,
                    SUM(ail.total_weight) as total_weight
                    FROM account_invoice_line ail
                    LEFT JOIN product_product pp ON pp.id=ail.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                    LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                    WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND (ai.not_accumulate=False OR ai.not_accumulate is NULL ) AND ail.partner_id="""+partner_id+""" AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                    AND ai.user_id not in (90) AND ail.uom_id not in (24) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
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
                    SUM(ail.quantity*(ail.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=ai.date_applied AND rcr.currency_id=ai.currency_id AND rcr.company_id=ai.company_id)))) as subtotal,
                    SUM(ail.total_weight) as total_weight
                    FROM account_invoice_line ail
                    LEFT JOIN product_product pp ON pp.id=ail.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                    LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                    WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND ail.partner_id="""+partner_id+""" AND ai.date_applied >= '"""+date_f+"""' AND ai.date_applied <= '"""+date_t+"""'
                    AND ai.user_id not in (90) AND ail.uom_id not in (24) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
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
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""
            (SELECT
                    rp.name as cliente,
                    rp.id,
                    COALESCE(tbs.kg_per_month,0) as ton
                    FROM trend_budget_sales tbs
                    LEFT JOIN res_partner rp ON rp.id=tbs.name
                    WHERE tbs.date_from >= '"""+date_from+"""' AND tbs.date_to <= '"""+str(df)+"""' AND rp.name not ilike 'ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.%'
                    GROUP BY rp.name,rp.id,tbs.kg_per_month
                    )
                    UNION
            (SELECT
                    rp.name as cliente,
                    rp.id,
                    COALESCE(tbs.kg_per_month,0) as ton
                    FROM budget_budget_sales bbs
                    LEFT JOIN res_partner rp ON rp.id=bbs.name
                    LEFT JOIN trend_budget_sales tbs ON tbs.name=rp.id
                    WHERE bbs.date_from >= '"""+date_from+"""' AND bbs.date_to <= '"""+str(df)+"""' AND rp.name not ilike 'ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.%'
                    GROUP BY rp.name,rp.id,tbs.kg_per_month
            )
                    UNION
                    (
            SELECT
                    rp.name as cliente,
                    rp.id,
                    COALESCE(tbs.kg_per_month,0) as ton
                    FROM account_invoice_line ail
                    LEFT JOIN product_product pp ON pp.id=ail.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                    LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                    LEFT JOIN trend_budget_sales tbs ON tbs.name=rp.id
                    WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                    AND ai.user_id not in (90) AND ail.uom_id not in (24) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%' AND rp.name not ilike 'ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.%'
                    GROUP BY rp.name,rp.id,tbs.kg_per_month

                    )
                    ORDER BY ton DESC
        """
        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _partner_trendArchi(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""
                (SELECT
                    rp.name as cliente,
                    rp.id,
                    COALESCE(tbs.kg_per_month,0) as ton
                    FROM trend_budget_sales tbs
                    LEFT JOIN res_partner rp ON rp.id=tbs.name
                    WHERE tbs.date_from >= '"""+date_from+"""' AND tbs.date_to <= '"""+str(df)+"""' AND rp.name ilike 'ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.%'
                    GROUP BY rp.name,rp.id,tbs.kg_per_month
                )
                    UNION
                (SELECT
                    rp.name as cliente,
                    rp.id,
                    COALESCE(tbs.kg_per_month,0) as ton
                    FROM budget_budget_sales bbs
                    LEFT JOIN res_partner rp ON rp.id=bbs.name
                    LEFT JOIN trend_budget_sales tbs ON tbs.name=rp.id
                    WHERE bbs.date_from >= '"""+date_from+"""' AND bbs.date_to <= '"""+str(df)+"""' AND rp.name ilike 'ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.%'
                    GROUP BY rp.name,rp.id,tbs.kg_per_month
                )
                    UNION
                (SELECT
                    rp.name as cliente,
                    rp.id,
                    COALESCE(tbs.kg_per_month,0) as ton
                    FROM account_invoice_line ail
                    LEFT JOIN product_product pp ON pp.id=ail.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                    LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                    LEFT JOIN trend_budget_sales tbs ON tbs.name=rp.id
                    WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                    AND ai.user_id not in (90) AND ail.uom_id not in (24) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%' AND rp.name ilike 'ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.%'
                    GROUP BY rp.name,rp.id,tbs.kg_per_month
                )
                    ORDER BY ton DESC
        """
        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchall()
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
        contadorinv=0

        estimado=0
        presupuesto=0
        facturacion=0
        tprice_per_kgp=0
        tprice_per_kgf=0
        tavancetons=0
        tdesvton=0
        tdesvpricekg=0
        ttendtonsfm=0
        tpromprevyear=0
        tmesprevyear=0
        tprojectventas=0
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

        ],
        })
        desv_price_per_kg=0
        if invoices:
            contadorinv=len(invoices)
            for invoice in invoices:
                budget=self._get_budget_sales(invoice[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                budget_budget=self._get_budget_budget_sales(invoice[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                project_sale=self._get_project_user_sales(invoice[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                comentarios = self.env['project.user.sales'].search(['&','&',('name','=',invoice[1]),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))])
                invoices_line=self._invoice_line_partner(options,line_id,str(invoice[1]))
                invoices_line_promedio=self._invoice_line_partner_n(options,line_id,str(invoice[1]), str(first_day_previous_fy),str(last_day_previous_fy))
                invoices_line_lymonth=self._invoice_line_partner_n(options,line_id,str(invoice[1]),str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))
                price_per_kg=self._get_budget_sales_price(invoice[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
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

                lines.append({
                        'id': str(invoice[0]),
                        'name': str(invoice[0]),
                        'level': 2,
                        'class': 'activo',
                        'columns':[
                            {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line[2]/1000))},
                            {'name':"{:.0%}".format(0) if budget==0 else "{:.0%}".format((invoices_line[2]/1000)/(budget/1000))},
                            {'name':"{:.0%}".format(0) if budget==0 else "{:.0%}".format(((invoices_line[2]/1000)/(((budget/1000)/bussines_days.bussines_days)*self._billed_days(options,line_id))-1))},
                            {'name':0 if self._billed_days(options,line_id)==0 or budget==False else "{:,}".format(round(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days))},
                            {'name':(0 if self._billed_days(options,line_id)==0 or budget==False else "{:,}".format(round(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days))) if project_sale==False else "{:,}".format(round(project_sale/1000)) },
                            {'name':'' if comentarios.note==False else comentarios.note},
                            {'name':0 if price_per_kg==False else self.format_value(price_per_kg) },
                            {'name':0 if invoices_line[2]==0 else self.format_value(invoices_line[1]/invoices_line[2])},
                            {'name':"{:.0%}".format(desv_price_per_kg) },
                            {'name':0 if budget_budget==False else "{:,}".format(round(budget_budget/1000)) },
                            {'name':0 if invoices_line_promedio[2]==0 else "{:,}".format(round((invoices_line_promedio[2]/12)/1000)) },
                            {'name':"{:,}".format(round((invoices_line_lymonth[2])/1000)) },

                        ],
                        })

                estimado+=budget/1000
                presupuesto+=budget_budget/1000
                facturacion+=invoices_line[2]/1000
                tprice_per_kgp+=price_per_kg/contadorinv
                if invoices_line[2]!=0:
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




            lines.append({
                    'id': 'total',
                    'name': 'TOTAL',
                    'level': 0,
                    'class': 'total',
                    'columns':[
                    {'name': "{:,}".format(round(estimado))},
                    {'name': "{:,}".format(round(facturacion))},
                    {'name':"{:.0%}".format(tavancetons)},
                    {'name':"{:.0%}".format(tdesvton)},
                    {'name':"{:,}".format(round(ttendtonsfm))},
                    {'name':"{:,}".format(round(tprojectventas))},
                    {'name':''},
                    {'name': self.format_value(tprice_per_kgp)},
                    {'name':self.format_value(tprice_per_kgf)},
                    {'name':"{:.0%}".format(tdesvpricekg)},
                    {'name': "{:,}".format(round(presupuesto))},
                    {'name':"{:,}".format(round(tpromprevyear))},
                    {'name':"{:,}".format(round(tmesprevyear))},
                    ],
                    })

        if invoicesarchi:

            for invoice in invoicesarchi:
                budget=self._get_budget_sales(invoice[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                budget_budget=self._get_budget_budget_sales(invoice[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                project_sale=self._get_project_user_sales(invoice[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                comentarios = self.env['project.user.sales'].search(['&','&',('name','=',invoice[1]),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))])
                invoices_line=self._invoice_line_partner(options,line_id,str(invoice[1]))
                invoices_line_promedio=self._invoice_line_partner_n(options,line_id,str(invoice[1]), str(first_day_previous_fy),str(last_day_previous_fy))
                invoices_line_lymonth=self._invoice_line_partner_n(options,line_id,str(invoice[1]),str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))
                price_per_kg=self._get_budget_sales_price(invoice[1], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
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

                lines.append({
                        'id': str(invoice[0]),
                        'name': str(invoice[0]),
                        'level': 0,
                        'class': 'activo',
                        'columns':[
                            {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line[2]/1000))},
                            {'name':"{:.0%}".format(0) if budget==0 else "{:.0%}".format((invoices_line[2]/1000)/(budget/1000))},
                            {'name':"{:.0%}".format(0) if budget==0 else "{:.0%}".format(((invoices_line[2]/1000)/(((budget/1000)/bussines_days.bussines_days)*self._billed_days(options,line_id))-1))},
                            {'name':0 if self._billed_days(options,line_id)==0 or budget==False else "{:,}".format(round(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days))},
                            {'name':(0 if self._billed_days(options,line_id)==0 or budget==False else "{:,}".format(round(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days))) if project_sale==False else "{:,}".format(round(project_sale/1000)) },
                            {'name':'' if comentarios.note==False else comentarios.note},
                            {'name':0 if price_per_kg==False else self.format_value(price_per_kg) },
                            {'name':0 if invoices_line[2]==0 else self.format_value(invoices_line[1]/invoices_line[2])},
                            {'name':"{:.0%}".format(desv_price_per_kg) },
                            {'name':0 if budget_budget==False else "{:,}".format(round(budget_budget/1000)) },
                            {'name':0 if invoices_line_promedio[2]==0 else "{:,}".format(round((invoices_line_promedio[2]/12)/1000)) },
                            {'name':"{:,}".format(round((invoices_line_lymonth[2])/1000)) },

                        ],
                        })

        #     for invoice in invoices:
        #         lines.append({
        #         'id': invoice.id,
        #         'name': invoice.partner_id.name,
        #         'level': 2,
        #         'class': 'activo',
        #         'columns':[
        #
        #         ],
        #         })
        #         for invoice_line in invoice.invoice_line_ids:
        #             if invoice_line.product_id.sale_ok == True:
        #                 lines.append({
        #                 'id': invoice_line.id,
        #                 'name': invoice_line.product_id.default_code,
        #                 'level': 3,
        #                 'class': 'activo',
        #                 'columns':[
        #                     {'name':"{:,}".format(invoice_line.quantity)},
        #                     {'name':self.format_value(invoice_line.price_unit*invoice.type_currency)},
        #                     {'name':"{:,}".format(invoice_line.weight)},
        #                     {'name':str(invoice_line.uom_id.name)+' '+str(invoice_line.uom_id.id)},
        #                     {'name':self.format_value(invoice_line.quantity*(invoice_line.price_unit*invoice.type_currency))},
        #                     {'name':"{:,}".format(invoice_line.quantity*invoice_line.weight)},
        #                     {'name': 0 if invoice_line.weight==False else self.format_value((invoice_line.quantity*(invoice_line.price_unit*invoice.type_currency))/(invoice_line.quantity*invoice_line.weight))},
        #                 ],
        #                 })


        return lines

    @api.model
    def _get_report_name(self):
        return _('Tendencia de Ventas')
