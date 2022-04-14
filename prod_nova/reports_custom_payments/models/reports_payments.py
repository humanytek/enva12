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


class ReportsPayments(models.AbstractModel):
    _name = "report.payments.nova"
    _description = "Reports Payments"
    _inherit = 'account.report'

    filter_date = {'mode': 'range', 'filter':'custom','date_from': '2021-05-30', 'date_to': '2021-05-30'}


    def _get_columns_name(self, options):
        return [
        {'name': _('FECHA'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('FOLIO'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('PROVEEDOR'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('MONTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('MONEDA'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('FACTURA'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('FECHA FACTURA'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('CIRCULAR'), 'class': 'number', 'style': 'text-align: left;white-space:nowrap;'},
        {'name': _('DESCRIPCION'), 'class': 'number', 'style': 'text-align: left;white-space:nowrap;'},

        ]

    def _payment_line(self,options,line_id,partner):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        sql_query ="""
            SELECT
                    ap.id as payment_id,
                    am.name as referencia_pago,
                    am.date as fecha_pago,
                    am.ref as circular,
                    rp.name as partner,
                    ap.amount as monto,
                    rc.name as moneda,
                    line.id as aml_id
                    FROM account_payment ap
                    JOIN account_move am ON am.id=ap.move_id
                    JOIN res_partner rp ON rp.id=ap.partner_id
                    JOIN res_currency rc ON rc.id=ap.currency_id
                    JOIN account_move_line line ON line.move_id = am.id
                    JOIN account_account account ON account.id = line.account_id
                    WHERE am.date >= '"""+date_from+"""' AND am.date <= '"""+date_to+"""'
                    AND am.state in ('posted') AND account.internal_type IN ('payable')
        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _invoice_aml(self,options,line_id,aml_id):

        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        sql_query ="""
              SELECT
                     ap.id as payment_id,
                     line.id as aml_id,
                     invoice.id as invoice_id,
                     invoice.name as invoice_name,
                     invoice.invoice_date as fecha_factura,
                     iline.id as iaml_id,
                     invoice.ref as referencia
                     FROM account_payment ap
                     JOIN account_move am ON am.id=ap.move_id
                     JOIN res_partner rp ON rp.id=ap.partner_id
                     JOIN res_currency rc ON rc.id=ap.currency_id
                     JOIN account_move_line line ON line.move_id = am.id
                     JOIN account_partial_reconcile part ON
                         part.debit_move_id = line.id
                         OR
                         part.credit_move_id = line.id
                     JOIN account_move_line counterpart_line ON
                         part.debit_move_id = counterpart_line.id
                         OR
                         part.credit_move_id = counterpart_line.id
                     JOIN account_move invoice ON invoice.id = counterpart_line.move_id
                     JOIN account_move_line iline ON iline.move_id = invoice.id
                     JOIN account_account account ON account.id = line.account_id

                     WHERE line.id = """+aml_id+"""
                     AND line.id != counterpart_line.id
                     AND am.state in ('posted') AND account.internal_type IN ('payable')
                     Limit 1
                                """


        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchall()

        return result

    def _payment_aml(self,options,line_id,payment_id,full_reconcile_id):


        sql_query ="""
              SELECT  aml.id as aml_id,
                      aml.debit as debit,
                      aml.amount_currency as amount_currency
                      FROM account_move_line aml
                      WHERE aml.payment_id = """+payment_id+""" AND aml.full_reconcile_id = """+full_reconcile_id+"""
                      AND aml.credit = 0 AND aml.debit > 0 """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _payment_amlf(self,options,line_id,payment_id,factura):


        sql_query ="""
              SELECT  aml.id as aml_id,
                      aml.debit as debit,
                      aml.amount_currency as amount_currency
                      FROM account_move_line aml
                      WHERE aml.payment_id = """+payment_id+""" AND aml.name = '"""+factura+"""' AND
                      aml.credit = 0 AND aml.debit > 0 """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _payment_aml2(self,options,line_id,payment_id):


        sql_query ="""
              SELECT
                      aml.id as aml_id
                      FROM account_move_line aml
                      WHERE aml.payment_id = """+payment_id+""" limit 1"""

        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchall()

        return result

    @api.model
    def _get_lines(self, options, line_id=None):

        lines = []
        pagos = self._payment_line(options,line_id,False)
        if pagos:
            for p in pagos:
                caret_type ='account.move'
                aml = self._invoice_aml(options,line_id,str(p['aml_id']))
                factura = ''
                fecha_factura = ''
                referencia = ''
                if aml:
                    aml_id=aml[0][5]
                    caret_type = 'account.move'
                    factura=str(aml[0][3])
                    fecha_factura=str(aml[0][4])
                    referencia=str(aml[0][6])
                else:
                    aml_id=p['aml_id']
                    caret_type = 'account.payment'



                lines.append({
                'id':aml_id,
                'name': str(p['fecha_pago']),
                'style': 'text-align: left; white-space:nowrap;',
                'level': 2,
                'class': 'payment',
                'caret_options': caret_type,
                'columns':[
                        {'name':str(p['referencia_pago']), 'style': 'text-align: left; white-space:nowrap;'},
                        {'name':str(p['partner']), 'style': 'text-align: left; white-space:nowrap;'},
                        {'name':self.format_value(p['monto'])},
                        {'name':str(p['moneda'])},
                        {'name':factura},
                        {'name':fecha_factura},
                        {'name':str(p['circular']), 'style': 'text-align: left; white-space:nowrap;'},
                        {'name':referencia},
                        # # {'name':self.format_value(monto) if p['factura'] != None else self.format_value(p['monto'])},

                        # {'name':str(p['factura']) if p['factura'] != None else '' , 'style': 'text-align: left; white-space:nowrap;'},
                        # {'name':str(p['fecha_factura']) if p['factura'] != None else '', 'style': 'text-align: left; white-space:nowrap;'},

                        # {'name':str(p['descripcion']), 'style': 'text-align: left; white-space:nowrap;'},
                        # {'name':str(p['descripcion']) if ail else '', 'style': 'text-align: left; white-space:nowrap;'},

                ],

                })
        return lines

    @api.model
    def _get_report_name(self):
        return _('Reportes de Pagos')
