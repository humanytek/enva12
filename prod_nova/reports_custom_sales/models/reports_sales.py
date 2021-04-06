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
        {'name': _('CANTIDAD'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO UNITARIO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PESO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('UM'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('VOLUMEN PRESUPUESTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('VOLUMEN REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('TENDENCIA'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PROMEDIO AÑO ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('MES AÑO ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO x KG PPTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO x KG REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
        ]



    # def _balance_initial(self,options,line_id,arg):
    #     tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
    #     if where_clause:
    #         where_clause = 'AND ' + where_clause
    #
    #     sql_query ="""
    #         SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
    #             FROM """+tables+"""
    #             LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
    #             WHERE aa.group_id = %s """+where_clause+"""
    #             GROUP BY aa.group_id
    #     """
    #     params = [str(arg)] + where_params
    #
    #     self.env.cr.execute(sql_query, params)
    #     result = self.env.cr.fetchone()
    #     if result==None:
    #         result=(0,)
    #
    #     return result

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        invoices=self.env['account.invoice'].search([('type','in',['out_invoice']),('state','in',['open','in_payment','paid']),('date_applied','>=',date_from),('date_applied','<=',date_to)],order='date_applied')
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
                lines.append({
                'id': invoice.id,
                'name': invoice.partner_id.name,
                'level': 2,
                'class': 'activo',
                'columns':[

                ],
                })
                for invoice_line in invoice.invoice_line_ids:
                    if invoice_line.product_id.sale_ok == True:
                        lines.append({
                        'id': invoice_line.id,
                        'name': invoice_line.product_id.default_code,
                        'level': 3,
                        'class': 'activo',
                        'columns':[
                            {'name':invoice_line.quantity},
                            {'name':invoice_line.price_unit},
                            {'name':invoice_line.weight},
                            {'name':invoice_line.uom_id.name +' '+invoice_line.uom_id.id},
                        ],
                        })


        return lines

    @api.model
    def _get_report_name(self):
        return _('Tendencia de Ventas')
