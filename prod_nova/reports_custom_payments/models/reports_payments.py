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

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}

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
                    ap.name as name,
                    ap.payment_date as fecha_pago,
                    ap.communication as circular,
                    rp.name as partner,
                    rp.id as partner_id,
                    ai.date_invoice as fecha_factura,
                    ai.number as factura,
                    ai.id as invoice_id,
                    rc.name as moneda,
                    ap.amount as monto
                    FROM account_payment ap
                    LEFT JOIN account_invoice_payment_rel aipr ON aipr.payment_id=ap.id
                    LEFT JOIN account_invoice ai ON ai.id=aipr.invoice_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_currency rc ON rc.id=ap.currency_id

                    WHERE ap.payment_date >= '"""+date_from+"""' AND ap.payment_date <= '"""+date_to+"""'
                    AND ap.state in ('posted','reconciled') AND ap.payment_type in ('outbound')

                    ORDER BY rp.name,ap.payment_date,ap.name


        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result


    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        pagos = self._payment_line(options,line_id,False)
        if pagos:
            for p in pagos:
                amlpaid=self.env['account.move.line'].search([('payment_id','=',p['payment_id'])],limit=1)
                caret_type ='account.move'
                if p['factura'] != None:
                    caret_type = 'account.invoice.in'
                    aml=self.env['account.move.line'].search(['&','&','&',('invoice_id','=',p['invoice_id']),('reconciled','=',True),('credit', '>', 0), ('debit', '=', 0)])
                    monto=0
                    if aml:
                        aml2=self.env['account.move.line'].search(['&','&','&','&',('payment_id','=',p['payment_id']),('full_reconcile_id','=',aml.full_reconcile_id.id),('reconciled','=',True),('debit', '>', 0), ('credit', '=', 0)])
                        if p['moneda']=='MXN':
                            if aml2:
                                for a in aml2:
                                    monto+=a.debit
                            else:
                                monto=0
                        else:
                            if aml2:
                                for a in aml2:
                                    monto+=a.amount_currency
                            else:
                                monto=0

                else:
                    caret_type = 'account.payment'
                    aml=amlpaid

                lines.append({
                'id': aml.id,
                'name': str(p['fecha_pago']) ,
                'level': 2,
                'class': 'payment',
                'caret_options': caret_type,
                'columns':[
                        {'name':str(p['name']), 'style': 'text-align: left; white-space:nowrap;'},
                        {'name':str(p['partner']), 'style': 'text-align: left; white-space:nowrap;'},
                        {'name':self.format_value(monto) if p['factura'] != None else self.format_value(p['monto'])},
                        {'name':str(p['moneda'])},
                        {'name':str(p['factura']) if p['factura'] != None else '' , 'style': 'text-align: left; white-space:nowrap;'},
                        {'name':str(p['fecha_factura']) if p['factura'] != None else '', 'style': 'text-align: left; white-space:nowrap;'},
                        {'name':str(p['circular']), 'style': 'text-align: left; white-space:nowrap;'},



                ],

                })
        return lines

    @api.model
    def _get_report_name(self):
        return _('Reportes de Pagos')
