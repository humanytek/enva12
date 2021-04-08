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
        {'name': _('VOLUMEN PRESUPUESTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('VOLUMEN REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('SUBTOTAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO x KG REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('TENDENCIA'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PROMEDIO AÑO ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('MES AÑO ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO x KG PPTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO x KG REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
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
                    WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND ail.partner_id="""+partner_id+""" AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                    AND ai.user_id not in (90) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                    GROUP BY rp.name
                    ORDER BY rp.name ASC
        """


        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchone()
        if result==None:
            result=('',0,0)

        return result

    def _partner_trend(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        sql_query ="""
            (SELECT
                    rp.name as cliente,
                    rp.id
                    FROM account_invoice_line ail
                    LEFT JOIN product_product pp ON pp.id=ail.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                    LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                    WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                    AND ai.user_id not in (90) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                    GROUP BY rp.name,rp.id)
                    UNION
                    (SELECT
                    rp.name as cliente,
                    rp.id
                    FROM trend_budget_sales tbs
                    LEFT JOIN res_partner rp ON rp.id=tbs.name
                    WHERE tbs.date_from >= '"""+date_from+"""' AND tbs.date_to <= '"""+date_to+"""'
                    )
                    ORDER BY cliente ASC
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


    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        invoices = self._partner_trend(options,line_id)

        # invoices=self.env['account.invoice'].search([('type','in',['out_invoice']),('state','in',['open','in_payment','paid']),('date_applied','>=',date_from),('date_applied','<=',date_to)],order='partner_id ASC,date_applied')
        lines.append({
        'id': 'cliente',
        'name': 'CLIENTE',
        'level': 0,
        'class': 'cliente',
        'columns':[

        ],
        })

        if invoices:
            for invoice in invoices:
                budget=self._get_budget_sales(invoice[1], fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                invoices_line=self._invoice_line_partner(options,line_id,str(invoice[1]))

                lines.append({
                        'id': str(invoice[0]),
                        'name': str(invoice[0]),
                        'level': 2,
                        'class': 'activo',
                        'columns':[
                            {'name':0 if budget==False else "{:,.2f}".format(budget/1000) },
                            {'name':"{:,.2f}".format(invoices_line[2]/1000)},
                            {'name':self.format_value(invoices_line[1])},
                            {'name':0 if invoices_line[2]==0 else self.format_value(invoices_line[1]/invoices_line[2])},

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
