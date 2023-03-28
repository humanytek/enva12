# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import time
from odoo import api, models, fields, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.addons.web.controllers.main import clean_action
_logger = logging.getLogger(__name__)


class ReportsBanks(models.AbstractModel):
    _name = "report.bank.nova"
    _description = "Reports Banks"
    _inherit = 'account.report'

    filter_date = {'mode': 'range', 'filter': 'this_month'}

    def _get_templates(self):
        templates = super(ReportsBanks, self)._get_templates()
        templates['line_template'] = 'reports_custom_bank.line_template_nova_banks'
        return templates

    def _get_columns_name(self, options):
        return [
            {'name': _(''), 'class': 'number',
             'style': 'text-align: center; white-space:nowrap;'},
            {'name': _('SALDO INICIAL'), 'class': 'number',
             'style': 'text-align: center; white-space:nowrap;'},
            {'name': _('TRASPASOS'), 'class': 'number',
             'style': 'text-align: center; white-space:nowrap;'},
            # {'name': _('ABONOS'), 'class': 'number', 'style':  'text-align: center; white-space:nowrap;'},
            {'name': _('INGRESOS'), 'class': 'number',
             'style': 'text-align: center; white-space:nowrap;'},
            {'name': _('PAGOS'), 'class': 'number',
             'style': 'text-align: center; white-space:nowrap;'},
            {'name': _('SALDO DIVISA'), 'class': 'number',
             'style': 'text-align: center; white-space:nowrap;'},
            {'name': _('SALDO MXN'), 'class': 'number',
             'style': 'text-align: center; white-space:nowrap;'},

        ]

    def _balance_initial(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+"""
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _receivables(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id is not Null )
                AND (\"account_move_line\".partner_id != 1)
                AND rpc.name IN ('CORRUGADO','PAPEL')
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _payments(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id != 1)
                AND (\"account_move_line\".partner_id is not Null)
                AND \"account_move_line\".partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=\"account_move_line\".partner_id LIMIT 1)
                
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _transfer_in(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id = 1 OR \"account_move_line\".partner_id is Null)
                
                GROUP BY aa.id,\"account_move_line\".partner_id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _transfer_out(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id = 1 OR \"account_move_line\".partner_id is Null)
                
                GROUP BY aa.id,\"account_move_line\".partner_id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _comision(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is not Null )
                AND \"account_move_line\".partner_id IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=\"account_move_line\".partner_id LIMIT 1)
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _interes(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id is not Null )
                AND \"account_move_line\".partner_id IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=\"account_move_line\".partner_id LIMIT 1)
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _transfer_inext(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id = 1 OR \"account_move_line\".partner_id is Null )
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _transfer_outext(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id = 1 OR \"account_move_line\".partner_id is Null )
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _comisionext(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is not Null )
                AND \"account_move_line\".partner_id IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=\"account_move_line\".partner_id LIMIT 1)
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _devoluciones(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance

                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id is not Null)
                AND (\"account_move_line\".partner_id != 1)
                AND rp.id NOT IN (SELECT rp.id
                                FROM res_partner_category rpc
                                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.category_id=rpc.id
                                 WHERE rp.id=rpcr.partner_id AND rpc.name IN ('CORRUGADO','PAPEL') Limit 1)
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0, 0,)

        return result

    def _paymentsext(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is not Null )
                AND (\"account_move_line\".partner_id != 1)
                AND \"account_move_line\".partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=\"account_move_line\".partner_id LIMIT 1)
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _receivablesext(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id is not Null )
                AND (\"account_move_line\".partner_id != 1)
                AND rpc.name IN ('CORRUGADO','PAPEL')
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _receivablesext_det(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT \"account_move_line\".date, rp.name as cliente,\"account_move_line\".name as etiqueta, COALESCE(\"account_move_line\".amount_currency,0) as balance,
                   case when rpc.name = 'CORRUGADO' then 'Cartón' when rpc.name = 'PAPEL' then 'Papel' end as tipo
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id is not Null )
                AND (\"account_move_line\".partner_id != 1)
                AND rpc.name IN ('CORRUGADO','PAPEL')
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.dictfetchall()
        if len(result) == 0:
            result = []
        return result

    def _receivables_det(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT \"account_move_line\".date, rp.name as cliente,\"account_move_line\".name as etiqueta, COALESCE(\"account_move_line\".balance,0) as balance,
                   case when rpc.name = 'CORRUGADO' then 'Cartón' when rpc.name = 'PAPEL' then 'Papel' end as tipo
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id is not Null )
                AND (\"account_move_line\".partner_id != 1)
                AND rpc.name IN ('CORRUGADO','PAPEL')
                order by rpc.name asc
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.dictfetchall()
        if len(result) == 0:
            result = []
        return result

    def _paymentsext_det(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT \"account_move_line\".date, rp.name as cliente,\"account_move_line\".name as etiqueta, COALESCE(\"account_move_line\".amount_currency,0) as balance,
                    'Cartera' as tipo
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id   
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is not Null )
                AND (\"account_move_line\".partner_id != 1)
                AND \"account_move_line\".partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=\"account_move_line\".partner_id LIMIT 1)
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.dictfetchall()
        if len(result) == 0:
            result = []
        return result

    def _payments_det(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT \"account_move_line\".date, rp.name as cliente,\"account_move_line\".name as etiqueta, COALESCE(\"account_move_line\".balance,0) as balance,
                    'Cartera' as tipo
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id   
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is not Null )
                AND (\"account_move_line\".partner_id != 1)
                AND \"account_move_line\".partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=\"account_move_line\".partner_id LIMIT 1)
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.dictfetchall()
        if len(result) == 0:
            result = []
        return result

    def _balance_initialext(self, options, line_id, arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(
            strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+"""
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _balance_service(self, options, date_from, banco):
        sql_query = """SELECT COALESCE(SUM(initial_balance),0) as balance
                     FROM bank_balance_nova
                     WHERE account = 'SERVICIOS PENINSULARES INDUSTRIALES DEL SURESTE SA DE CV'
                     AND name <='""" + str(date_from)+"""' AND bank = '""" + str(banco)+"""'"""
        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    def _balance_industrial(self, options, date_from, banco):
        sql_query = """SELECT COALESCE(SUM(initial_balance),0) as balance
                     FROM bank_balance_nova
                     WHERE account = 'INDUSTRIAL CONSULTING SCP'
                     AND name <='""" + str(date_from)+"""' AND bank = '""" + str(banco)+"""'"""
        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchone()
        if result == None:
            result = (0,)

        return result

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        tipo_cambio_usd = self.env['res.currency.rate'].search(
            ['&', ('currency_id', '=', 2), ('name', '=', fields.Date.from_string(date_from))])
        tipo_cambio_euro = self.env['res.currency.rate'].search(
            ['&', ('currency_id', '=', 1), ('name', '=', fields.Date.from_string(date_from))])
        saldo_final_mxn = 0
        saldo_final_usd = 0
        saldo_final_euro = 0
        pagos_mxn = 0
        pagos_usd = 0
        pagos_euro = 0
        total_mxn = 0
        total_usd = 0
        total_euro = 0
        balance_init4 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initialext(options, line_id, str('102.01.220'))
        balance_final4 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initialext(options, line_id, str('102.01.220'))
        pagos4 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._paymentsext(options, line_id, str('102.01.220'))
        ingresos4 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivablesext(options, line_id, str('102.01.220'))
        transfer_in4 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_inext(options, line_id, str('102.01.220'))
        transfer_out4 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_outext(options, line_id, str('102.01.220'))
        comision4 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comisionext(options, line_id, str('102.01.220'))
        lines.append({
            'id': '102.01.220',
            'name': 'BBVA BANCOMER 0100773034 USD',
            'level': 2,
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init4[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in4[0]+comision4[0]+transfer_out4[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(comision4[0]+transfer_out4[0])),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in4[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos4[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init4[0]+ingresos4[0]+comision4[0]+transfer_out4[0]+transfer_in4[0])},
                {'name': self.format_value(
                    abs(pagos4[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final4[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(balance_final4[0]*(1/tipo_cambio_usd.rate)) if tipo_cambio_usd else self.format_value(
                    balance_final4[0]*1), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        saldo_final_usd += balance_init4[0]+ingresos4[0] + \
            comision4[0]+transfer_out4[0]+transfer_in4[0]
        pagos_usd += pagos4[0]
        total_usd += balance_final4[0]
        balance_init5 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initialext(options, line_id, str('102.01.320'))
        balance_final5 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initialext(options, line_id, str('102.01.320'))
        pagos5 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._paymentsext(options, line_id, str('102.01.320'))
        ingresos5 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivablesext(options, line_id, str('102.01.320'))
        transfer_in5 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_inext(options, line_id, str('102.01.320'))
        transfer_out5 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_outext(options, line_id, str('102.01.320'))
        comision5 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comisionext(options, line_id, str('102.01.320'))
        lines.append({
            'id': '102.01.320',
            'name': 'BBVA BANCOMER 0196249760 EURO',
            'level': 2,
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init5[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in5[0]+comision5[0]+transfer_out5[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(comision5[0]+transfer_out5[0])),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in5[0]),'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos5[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init5[0]+ingresos5[0]+comision5[0]+transfer_out5[0]+transfer_in5[0])},
                {'name': self.format_value(
                    abs(pagos5[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final5[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(balance_final5[0]*(1/tipo_cambio_euro.rate)) if tipo_cambio_euro else self.format_value(
                    balance_final5[0]*1), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        saldo_final_euro += balance_init5[0]+ingresos5[0] + \
            comision5[0]+transfer_out5[0]+transfer_in5[0]
        pagos_euro += pagos5[0]
        total_euro += balance_final5[0]
        balance_init = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initial(options, line_id, str('102.01.120'))
        balance_final = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initial(options, line_id, str('102.01.120'))
        pagos = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments(options, line_id, str('102.01.120'))
        ingresos = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables(options, line_id, str('102.01.120'))
        transfer_in = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options, line_id, str('102.01.120'))
        transfer_out = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options, line_id, str('102.01.120'))
        comision = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comision(options, line_id, str('102.01.120'))
        devoluciones = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._devoluciones(options, line_id, str('102.01.120'))
        lines.append({
            'id': '102.01.120',
            'name': 'BBVA BANCOMER 0132940590 MN',
            'level': 2,
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init[0]), 'style': 'text-align: right; white-space:nowrap;', 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in[0]+devoluciones[0]+comision[0]+transfer_out[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(comision[0]+transfer_out[0])),'style': 'text-align: right; white-space:nowrap;','style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in[0]+devoluciones[0]),'style': 'text-align: right; white-space:nowrap;','style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos[0]), 'style': 'text-align: right; white-space:nowrap;', 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init[0]+ingresos[0]+comision[0]+transfer_out[0]+transfer_in[0])},
                {'name': self.format_value(abs(
                    pagos[0])), 'style': 'text-align: right; white-space:nowrap;', 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final[0]), 'style': 'text-align: right; white-space:nowrap;', 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final[0]), 'style': 'text-align: right; white-space:nowrap;', 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        saldo_final_mxn += balance_init[0]+ingresos[0] + \
            comision[0]+transfer_out[0]+transfer_in[0]
        pagos_mxn += pagos[0]
        total_mxn += balance_final[0]
        balance_init1 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initial(options, line_id, str('102.01.140'))
        balance_final1 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initial(options, line_id, str('102.01.140'))
        pagos1 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments(options, line_id, str('102.01.140'))
        ingresos1 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables(options, line_id, str('102.01.140'))
        devoluciones1 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._devoluciones(options, line_id, str('102.01.140'))
        transfer_in1 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options, line_id, str('102.01.140'))
        transfer_out1 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options, line_id, str('102.01.140'))
        comision1 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comision(options, line_id, str('102.01.140'))
        lines.append({
            'id': '102.01.140',
            'name': 'SANTANDER 65503315522 MN',
            'level': 2,
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init1[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in1[0]+devoluciones1[0]+comision1[0]+transfer_out1[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(transfer_out1[0]+comision1[0])),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in1[0]+devoluciones1[0]),'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos1[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init1[0]+ingresos1[0]+comision1[0]+transfer_out1[0]+transfer_in1[0])},
                {'name': self.format_value(
                    abs(pagos1[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final1[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final1[0]), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        saldo_final_mxn += balance_init1[0]+ingresos1[0] + \
            comision1[0]+transfer_out1[0]+transfer_in1[0]
        pagos_mxn += pagos1[0]
        total_mxn += balance_final1[0]
        balance_init2 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initial(options, line_id, str('102.01.160'))
        balance_final2 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initial(options, line_id, str('102.01.160'))
        pagos2 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments(options, line_id, str('102.01.160'))
        ingresos2 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables(options, line_id, str('102.01.160'))
        transfer_in2 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options, line_id, str('102.01.160'))
        transfer_out2 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options, line_id, str('102.01.160'))
        comision2 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comision(options, line_id, str('102.01.160'))
        devoluciones2 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._devoluciones(options, line_id, str('102.01.160'))

        lines.append({
            'id': '102.01.160',
            'name': 'MULTIVA 3879186 MN',
            'level': 2,
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init2[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in2[0]+devoluciones2[0]+comision2[0]+transfer_out2[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(transfer_out2[0]+comision2[0])),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in2[0]+devoluciones2[0]),'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos2[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init2[0]+ingresos2[0]+comision2[0]+transfer_out2[0]+transfer_in2[0])},
                {'name': self.format_value(
                    abs(pagos2[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final2[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final2[0]), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        saldo_final_mxn += balance_init2[0]+ingresos2[0] + \
            comision2[0]+transfer_out2[0]+transfer_in2[0]
        pagos_mxn += pagos2[0]
        total_mxn += balance_final2[0]
        balance_init6 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initial(options, line_id, str('102.01.150'))
        balance_final6 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initial(options, line_id, str('102.01.150'))
        pagos6 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments(options, line_id, str('102.01.150'))
        ingresos6 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables(options, line_id, str('102.01.150'))
        transfer_in6 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options, line_id, str('102.01.150'))
        transfer_out6 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options, line_id, str('102.01.150'))
        comision6 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comision(options, line_id, str('102.01.150'))
        lines.append({
            'id': '102.01.150',
            'name': 'BANBAJIO 0087999670201 MN',
            'level': 2,
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init6[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in6[0]+comision6[0]+transfer_out6[0]),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(transfer_out6[0]+comision6[0])),'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in6[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos6[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init6[0]+ingresos6[0]+comision6[0]+transfer_out6[0]+transfer_in6[0])},
                {'name': self.format_value(
                    abs(pagos6[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final6[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final6[0]), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        saldo_final_mxn += balance_init6[0]+ingresos6[0] + \
            comision6[0]+transfer_out6[0]+transfer_in6[0]
        pagos_mxn += pagos6[0]
        total_mxn += balance_final6[0]
        balance_init7 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initialext(options, line_id, str('102.01.350'))
        balance_final7 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initialext(options, line_id, str('102.01.350'))
        pagos7 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._paymentsext(options, line_id, str('102.01.350'))
        ingresos7 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivablesext(options, line_id, str('102.01.350'))
        transfer_in7 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_inext(options, line_id, str('102.01.350'))
        transfer_out7 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_outext(options, line_id, str('102.01.350'))
        comision7 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comisionext(options, line_id, str('102.01.350'))
        lines.append({
            'id': '102.01.350',
            'name': 'BANBAJIO 0087999671801 EURO',
            'level': 2,
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init7[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in7[0]+comision7[0]+transfer_out7[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(transfer_out7[0]+comision7[0])),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in7[0]),'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos7[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init7[0]+ingresos7[0]+comision7[0]+transfer_out7[0]+transfer_in7[0])},
                {'name': self.format_value(
                    abs(pagos7[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final7[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(balance_final7[0]*(1/tipo_cambio_euro.rate)) if tipo_cambio_euro else self.format_value(
                    balance_final7[0]*1), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        saldo_final_euro += balance_init7[0]+ingresos7[0] + \
            comision7[0]+transfer_out7[0]+transfer_in7[0]
        pagos_euro += pagos7[0]
        total_euro += balance_final7[0]
        balance_init8 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initial(options, line_id, str('102.01.170'))
        balance_final8 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initial(options, line_id, str('102.01.170'))
        pagos8 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments(options, line_id, str('102.01.170'))
        ingresos8 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables(options, line_id, str('102.01.170'))
        transfer_in8 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options, line_id, str('102.01.170'))
        transfer_out8 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options, line_id, str('102.01.170'))
        comision8 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comision(options, line_id, str('102.01.170'))
        lines.append({
            'id': '102.01.170',
            'name': 'BBASE 145691288080001018 MN',
            'level': 2,
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init8[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in8[0]+comision8[0]+transfer_out8[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(transfer_out8[0]+comision8[0])),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in8[0]),'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos8[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init8[0]+ingresos8[0]+comision8[0]+transfer_out8[0]+transfer_in8[0])},
                {'name': self.format_value(
                    abs(pagos8[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final8[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final8[0]), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        saldo_final_mxn += balance_init8[0]+ingresos8[0] + \
            comision8[0]+transfer_out8[0]+transfer_in8[0]
        pagos_mxn += pagos8[0]
        total_mxn += balance_final8[0]
        balance_init3 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initialext(options, line_id, str('102.01.270'))
        balance_final3 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initialext(options, line_id, str('102.01.270'))
        pagos3 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._paymentsext(options, line_id, str('102.01.270'))
        ingresos3 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivablesext(options, line_id, str('102.01.270'))
        transfer_in3 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_inext(options, line_id, str('102.01.270'))
        transfer_out3 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_outext(options, line_id, str('102.01.270'))
        comision3 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comisionext(options, line_id, str('102.01.270'))
        lines.append({
            'id': '102.01.270',
            'name': 'BBASE 145691288080002017 USD',
            'level': 2,
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init3[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in3[0]+comision3[0]+transfer_out3[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(transfer_out3[0]+comision3[0])),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in3[0]),'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos3[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init3[0]+ingresos3[0]+comision3[0]+transfer_out3[0]+transfer_in3[0])},
                {'name': self.format_value(
                    abs(pagos3[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final3[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(balance_final3[0]*(1/tipo_cambio_usd.rate)) if tipo_cambio_usd else self.format_value(
                    balance_final3[0]*1), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        saldo_final_usd += balance_init3[0]+ingresos3[0] + \
            comision3[0]+transfer_out3[0]+transfer_in3[0]
        pagos_usd += pagos3[0]
        total_usd += balance_final3[0]
        balance_init9 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initialext(options, line_id, str('102.01.370'))
        balance_final9 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initialext(options, line_id, str('102.01.370'))
        pagos9 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._paymentsext(options, line_id, str('102.01.370'))
        ingresos9 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivablesext(options, line_id, str('102.01.370'))
        transfer_in9 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_inext(options, line_id, str('102.01.370'))
        transfer_out9 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_outext(options, line_id, str('102.01.370'))
        comision9 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comisionext(options, line_id, str('102.01.370'))
        lines.append({
            'id': '102.01.270',
            'name': 'BBASE 145691288080013019 EURO',
            'level': 2,
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init9[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in9[0]+comision9[0]+transfer_out9[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(transfer_out9[0]+comision9[0])),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in9[0]),'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos9[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init9[0]+ingresos9[0]+comision9[0]+transfer_out9[0]+transfer_in9[0])},
                {'name': self.format_value(
                    abs(pagos9[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final9[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(balance_final9[0]*(1/tipo_cambio_euro.rate)) if tipo_cambio_euro else self.format_value(
                    balance_final9[0]*1), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        saldo_final_euro += balance_init9[0]+ingresos9[0] + \
            comision9[0]+transfer_out9[0]+transfer_in9[0]
        pagos_euro += pagos9[0]
        total_euro += balance_final9[0]
        balance_init10 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initial(options, line_id, str('103.01.001'))
        balance_final10 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initial(options, line_id, str('103.01.001'))
        balance_final10b = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initial(options, line_id, str('103.01.001'))
        pagos10 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments(options, line_id, str('103.01.001'))
        ingresos10 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables(options, line_id, str('103.01.001'))
        transfer_in10 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options, line_id, str('103.01.001'))
        transfer_out10 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options, line_id, str('103.01.001'))
        comision10 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comision(options, line_id, str('103.01.001'))
        interes10 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._interes(options, line_id, str('103.01.001'))
        lines.append({
            'id': '103.01.001',
            'name': 'MULTIVA INTEGRA  6469507',
            'level': 0,
            'style': 'border-style: none;',
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init10[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in10[0]+interes10[0]+comision10[0]+transfer_out10[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(transfer_out10[0]+comision10[0])),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in10[0]+interes10[0]),'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos10[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init10[0]+ingresos10[0]+comision10[0]+transfer_out10[0]+transfer_in10[0])},
                {'name': self.format_value(
                    abs(pagos10[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final10[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final10b[0]), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        total_mxn += balance_final10[0]
        balance_init11 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from) + timedelta(days=-1))._balance_initial(options, line_id, str('103.01.002'))
        balance_final11 = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initial(options, line_id, str('103.01.002'))
        balance_final11b = self.with_context(date_from=False, date_to=fields.Date.from_string(
            date_from))._balance_initial(options, line_id, str('103.01.002'))
        pagos11 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments(options, line_id, str('103.01.002'))
        ingresos11 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables(options, line_id, str('103.01.002'))
        transfer_in11 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options, line_id, str('103.01.002'))
        transfer_out11 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options, line_id, str('103.01.002'))
        comision11 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._comision(options, line_id, str('103.01.002'))
        interes11 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._interes(options, line_id, str('103.01.002'))
        lines.append({
            'id': '103.01.002',
            'name': 'INVERSIÓN FONDO DE AHORRO',
            'level': 0,
            'style': 'border-style: none;',
            'class': 'cuentas',
            'columns': [
                {'name': self.format_value(
                    balance_init11[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    transfer_in11[0]+interes11[0]+comision11[0]+transfer_out11[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(abs(transfer_out11[0]+comision11[0])),'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(transfer_in11[0]+interes11[0]),'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    ingresos11[0]), 'style': 'text-align: right; white-space:nowrap;'},
                # {'name':self.format_value(balance_init10[0]+ingresos10[0]+comision10[0]+transfer_out10[0]+transfer_in10[0])},
                {'name': self.format_value(
                    abs(pagos11[0])), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final11[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    balance_final11b[0]), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })
        total_mxn += balance_final11[0]
        lines.append({
            'id': 'TOTAL',
            'name': '',
            'level': 0,
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
            ],
        })
        lines.append({
            'id': 'TOTAL MN',
            'name': '',
            'level': 1,
            'style': 'border-style: none;',
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                # {'name':self.format_value(saldo_final_mxn)},
                # {'name':self.format_value(abs(pagos_mxn))},
                {'name': 'TOTAL M.N.:', 'style': 'text-align: right; white-space:nowrap;'},
                {'name': ''},
                {'name': self.format_value(
                    total_mxn), 'style': 'text-align: right; white-space:nowrap;'},

            ],
        })

        usd = 1
        if tipo_cambio_usd:
            usd = 1/tipo_cambio_usd.rate
            total_usd_to_mxn = total_usd*(1/tipo_cambio_usd.rate)
        else:
            total_usd_to_mxn = total_usd*(1/1)

        lines.append({
            'id': 'TOTAL USD',
            'name': 'Tipo de Cambio USD: ' + str(self.format_value(usd)),
            'level': 1,
            'style': 'border-style: none;',
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                # {'name':self.format_value(saldo_final_usd)},
                # {'name':self.format_value(abs(pagos_usd))},
                {'name': 'TOTAL USD:', 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    total_usd), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    total_usd_to_mxn), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })

        euro = 1
        if tipo_cambio_euro:
            euro = 1 / tipo_cambio_euro.rate
            total_euro_to_mxn = total_euro*(1/tipo_cambio_euro.rate)
        else:
            total_euro_to_mxn = total_euro*(1/1)

        lines.append({
            'id': 'TOTAL EURO',
            'name': 'Tipo de Cambio EURO: ' + str(self.format_value(euro)),
            'level': 1,
            'style': 'border-width: 3px;border-style: none none double none;',
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                # {'name':self.format_value(saldo_final_euro)},
                # {'name':self.format_value(abs(pagos_euro))},
                {'name': 'TOTAL EURO:', 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    total_euro), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    total_euro_to_mxn), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })

        lines.append({
            'id': 'TOTAL MN DISP',
            'name': '',
            'level': 1,
            'style': 'border-width: 3px;border-style: none none double none; font-size:15px;',
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': 'TOTAL EN M.N. DISP:',
                    'style': 'text-align: right; white-space:nowrap;'},
                {'name': ''},
                {'name': self.format_value(
                    total_mxn+total_usd_to_mxn+total_euro_to_mxn), 'style': 'text-align: right; white-space:nowrap;'},

            ],
        })

        lines.append({
            'id': 'Servicio',
            'name': 'SERVICIOS PENINSULARES INDUSTRIALES DEL SURESTE SA DE CV',
            'level': 1,
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
            ],
        })

        servicioInicial = self._balance_service(
            options, fields.Date.from_string(date_from) + timedelta(days=-1), 'BANCOMER')
        servicioFinal = self._balance_service(
            options, fields.Date.from_string(date_from), 'BANCOMER')

        lines.append({
            'id': 'Bancomer',
            'name': 'BANCOMER',
            'level': 2,
            'class': 'total',
            'columns': [
                {'name': self.format_value(
                    servicioInicial[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    servicioFinal[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    servicioFinal[0]), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })

        servicioInicial2 = self._balance_service(
            options, fields.Date.from_string(date_from) + timedelta(days=-1), 'SANTANDER')
        servicioFinal2 = self._balance_service(
            options, fields.Date.from_string(date_from), 'SANTANDER')

        lines.append({
            'id': 'Santander',
            'name': 'SANTANDER',
            'level': 2,
            'class': 'total',
            'columns': [
                {'name': self.format_value(
                    servicioInicial2[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    servicioFinal2[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    servicioFinal2[0]), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })

        lines.append({
            'id': 'Industrial',
            'name': 'INDUSTRIAL CONSULTING SCP',
            'level': 1,
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
            ],
        })

        servicioInicial3 = self._balance_industrial(
            options, fields.Date.from_string(date_from) + timedelta(days=-1), 'SANTANDER')
        servicioFinal3 = self._balance_industrial(
            options, fields.Date.from_string(date_from), 'SANTANDER')

        lines.append({
            'id': 'Santander',
            'name': 'SANTANDER',
            'level': 2,
            'class': 'total',
            'columns': [
                {'name': self.format_value(
                    servicioInicial3[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    servicioFinal3[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    servicioFinal3[0]), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })

        servicioInicial4 = self._balance_industrial(
            options, fields.Date.from_string(date_from) + timedelta(days=-1), 'MULTIVA')
        servicioFinal4 = self._balance_industrial(
            options, fields.Date.from_string(date_from), 'MULTIVA')

        lines.append({
            'id': 'Multiva',
            'name': 'MULTIVA',
            'level': 2,
            'class': 'total',
            'columns': [
                {'name': self.format_value(
                    servicioInicial4[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    0), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    servicioFinal4[0]), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    servicioFinal4[0]), 'style': 'text-align: right; white-space:nowrap;'},
            ],
        })

        total_manual = servicioFinal[0] + servicioFinal2[0] + \
            servicioFinal3[0]+servicioFinal4[0]

        lines.append({
            'id': 'TOTAL MN GRUPO',
            'name': '',
            'level': 1,
            'style': 'border-width: 3px;border-style: none none double none; font-size:15px;',
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': 'TOTAL GRUPO M.N.:',
                    'style': 'text-align: right; white-space:nowrap;'},
                {'name': ''},
                {'name': self.format_value(total_mxn+total_usd_to_mxn+total_euro_to_mxn +
                                           total_manual), 'style': 'text-align: right; white-space:nowrap;'},

            ],
        })

        lines.append({
            'id': 'empty',
            'name': '',
            'level': 0,
            'style': 'text-align: left;border-style: none;font-size:15px;',
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
            ],
        })

        lines.append({
            'id': 'Ingresos',
            'name': 'INGRESOS',
            'level': 0,
            'style': 'text-align: left;border-style: none;font-size:15px;',
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
            ],
        })

        lines.append({
            'id': 'Detalle',
            'name': '',
            'level': 1,
            'class': 'total',
            'columns': [
                {'name': 'CLIENTES'},
                {'name': 'ETIQUETA'},
                {'name': 'MONEDA'},
                {'name': 'MONTO DIVISA'},
                {'name': 'MONTO MXN'},
            ],
        })

        subIngreso = 0
        subMnxIngreso = 0
        detIngreso = self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(
            date_to))._receivablesext_det(options, line_id, str('102.01.220'))
        if len(detIngreso) > 0:
            lines.append({
                'id': '102.01.220',
                'name': 'BBVA BANCOMER 0100773034 USD',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d1 in detIngreso:
                montomxn = 0
                if tipo_cambio_usd:
                    montomxn = d1['balance']*(1/tipo_cambio_usd.rate)
                else:
                    montomxn = d1['balance']*(1/1)

                subIngreso += d1['balance']
                subMnxIngreso += montomxn
                lines.append({
                    'id': '102.01.220',
                    'name': d1['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d1['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d1['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'USD', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d1['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            montomxn), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso2 = self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(
            date_to))._receivablesext_det(options, line_id, str('102.01.320'))
        if len(detIngreso2) > 0:
            lines.append({
                'id': '102.01.320',
                'name': 'BBVA BANCOMER 0196249760 EURO',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d2 in detIngreso2:
                montomxn = 0
                if tipo_cambio_euro:
                    montomxn = d2['balance']*(1/tipo_cambio_euro.rate)
                else:
                    montomxn = d2['balance']*(1/1)
                subIngreso += d2['balance']
                subMnxIngreso += montomxn
                lines.append({
                    'id': '102.01.320',
                    'name': d2['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d2['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d2['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'EURO', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d2['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            montomxn), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso3 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables_det(options, line_id, str('102.01.120'))
        if len(detIngreso3) > 0:
            lines.append({
                'id': '102.01.120',
                'name': 'BBVA BANCOMER 0132940590 MN',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d3 in detIngreso3:
                subIngreso += d3['balance']
                subMnxIngreso += d3['balance']

                lines.append({
                    'id': '102.01.120',
                    'name': d3['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d3['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d3['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d3['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            d3['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso4 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables_det(options, line_id, str('102.01.140'))
        if len(detIngreso4) > 0:
            lines.append({
                'id': '102.01.140',
                'name': 'SANTANDER 65503315522 MN',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d4 in detIngreso4:
                subIngreso += d4['balance']
                subMnxIngreso += d4['balance']

                lines.append({
                    'id': '102.01.140',
                    'name': d4['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d4['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d4['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d4['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            d4['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso5 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables_det(options, line_id, str('102.01.160'))
        if len(detIngreso5) > 0:
            lines.append({
                'id': '102.01.160',
                'name': 'MULTIVA 3879186 MN',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d5 in detIngreso5:
                subIngreso += d5['balance']
                subMnxIngreso += d5['balance']

                lines.append({
                    'id': '102.01.160',
                    'name': d5['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d5['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d5['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d5['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            d5['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso6 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables_det(options, line_id, str('102.01.150'))
        if len(detIngreso6) > 0:
            lines.append({
                'id': '102.01.150',
                'name': 'BANBAJIO 0087999670201 MN',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d6 in detIngreso6:
                subIngreso += d6['balance']
                subMnxIngreso += d6['balance']

                lines.append({
                    'id': '102.01.150',
                    'name': d6['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d6['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d6['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d6['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            d6['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso7 = self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(
            date_to))._receivablesext_det(options, line_id, str('102.01.350'))
        if len(detIngreso7) > 0:
            lines.append({
                'id': '102.01.350',
                'name': 'BANBAJIO 0087999671801 EURO',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d7 in detIngreso7:
                montomxn = 0
                if tipo_cambio_euro:
                    montomxn = d7['balance']*(1/tipo_cambio_euro.rate)
                else:
                    montomxn = d7['balance']*(1/1)

                subIngreso += d7['balance']
                subMnxIngreso += montomxn
                lines.append({
                    'id': '102.01.350',
                    'name': d7['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d7['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d7['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'EURO', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d7['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            montomxn), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso8 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables_det(options, line_id, str('102.01.170'))
        if len(detIngreso8) > 0:
            lines.append({
                'id': '102.01.170',
                'name': 'BBASE 145691288080001018 MN',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d8 in detIngreso8:
                subIngreso += d8['balance']
                subMnxIngreso += d8['balance']
                lines.append({
                    'id': '102.01.170',
                    'name': d8['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d8['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d8['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d8['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            d8['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso9 = self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(
            date_to))._receivablesext_det(options, line_id, str('102.01.270'))
        if len(detIngreso9) > 0:
            lines.append({
                'id': '102.01.270',
                'name': 'BBASE 145691288080002017 USD',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d9 in detIngreso9:
                montomxn = 0
                if tipo_cambio_usd:
                    montomxn = d9['balance']*(1/tipo_cambio_usd.rate)
                else:
                    montomxn = d9['balance']*(1/1)
                subIngreso += d9['balance']
                subMnxIngreso += montomxn
                lines.append({
                    'id': '102.01.270',
                    'name': d9['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d9['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d9['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'USD', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d9['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            montomxn), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso10 = self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(
            date_to))._receivablesext_det(options, line_id, str('102.01.370'))
        if len(detIngreso10) > 0:
            lines.append({
                'id': '102.01.370',
                'name': 'BBASE 145691288080013019 EURO',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d10 in detIngreso10:
                montomxn = 0
                if tipo_cambio_euro:
                    montomxn = d10['balance']*(1/tipo_cambio_euro.rate)
                else:
                    montomxn = d10['balance']*(1/1)
                subIngreso += d10['balance']
                subMnxIngreso += montomxn
                lines.append({
                    'id': '102.01.350',
                    'name': d10['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d10['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d10['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'EURO', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d10['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            montomxn), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso11 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables_det(options, line_id, str('103.01.001'))
        if len(detIngreso11) > 0:
            lines.append({
                'id': '103.01.001',
                'name': 'MULTIVA INTEGRA 6469507',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d11 in detIngreso11:
                subIngreso += d11['balance']
                subMnxIngreso += d11['balance']
                lines.append({
                    'id': '103.01.001',
                    'name': d11['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d11['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d11['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d11['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            d11['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detIngreso12 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._receivables_det(options, line_id, str('103.01.002'))
        if len(detIngreso12) > 0:
            lines.append({
                'id': '103.01.002',
                'name': 'INVERSIÓN FONDO DE AHORRO',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d12 in detIngreso12:
                subIngreso += d12['balance']
                subMnxIngreso += d121['balance']

                lines.append({
                    'id': '103.01.002',
                    'name': d12['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d12['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d12['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            d12['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            d12['balance']), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        if subIngreso > 0:
            lines.append({
                'id': 'Subtotal',
                'name': '',
                'level': 1,
                'style': 'border-width: 3px;border-style: none none double none; font-size:15px;',
                'class': 'total',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': 'SUBTOTAL:',
                        'style': 'text-align: right; white-space:nowrap;'},
                    {'name': self.format_value(
                        subIngreso), 'style': 'text-align: right; white-space:nowrap;'},
                    {'name': self.format_value(
                        subMnxIngreso), 'style': 'text-align: right; white-space:nowrap;'},
                    {'name': ''},

                ],
            })

        lines.append({
            'id': 'Pagos',
            'name': 'PAGOS',
            'level': 0,
            'style': 'border-style: none;font-size:15px;',
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
            ],
        })

        lines.append({
            'id': 'Detalle',
            'name': '',
            'level': 1,
            'class': 'total',
            'columns': [
                {'name': 'PROVEDORES'},
                {'name': 'ETIQUETA'},
                {'name': 'MONEDA'},
                {'name': 'MONTO DIVISA'},
                {'name': 'MONTO MXN'},
            ],
        })

        subPago = 0
        subMxnPago = 0
        detPago = self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(
            date_to))._paymentsext_det(options, line_id, str('102.01.220'))
        if len(detPago) > 0:
            lines.append({
                'id': '102.01.220',
                'name': 'BBVA BANCOMER 0100773034 USD',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d1 in detPago:
                montomxn = 0
                if tipo_cambio_usd:
                    montomxn = d1['balance']*(1/tipo_cambio_usd.rate)
                else:
                    montomxn = d1['balance']*(1/1)

                subPago += d1['balance']
                subMxnPago += montomxn
                lines.append({
                    'id': '102.01.220',
                    'name': d1['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d1['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d1['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'USD', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d1['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(montomxn)), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago2 = self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(
            date_to))._paymentsext_det(options, line_id, str('102.01.320'))
        if len(detPago2) > 0:
            lines.append({
                'id': '102.01.320',
                'name': 'BBVA BANCOMER 0196249760 EURO',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d2 in detPago2:
                montomxn = 0
                if tipo_cambio_euro:
                    montomxn = d2['balance']*(1/tipo_cambio_euro.rate)
                else:
                    montomxn = d2['balance']*(1/1)

                subPago += d2['balance']
                subMxnPago += montomxn
                lines.append({
                    'id': '102.01.320',
                    'name': d2['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d2['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d2['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'EURO', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d2['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(montomxn)), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago3 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments_det(options, line_id, str('102.01.120'))
        if len(detPago3) > 0:
            lines.append({
                'id': '102.01.120',
                'name': 'BBVA BANCOMER 0132940590 MN',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d3 in detPago3:

                subPago += d3['balance']
                subMxnPago += d3['balance']

                lines.append({
                    'id': '102.01.120',
                    'name': d3['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d3['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d3['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d3['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d3['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago4 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments_det(options, line_id, str('102.01.140'))
        if len(detPago4) > 0:
            lines.append({
                'id': '102.01.140',
                'name': 'SANTANDER 65503315522 MN',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d4 in detPago4:

                subPago += d4['balance']
                subMxnPago += d4['balance']

                lines.append({
                    'id': '102.01.140',
                    'name': d4['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d4['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d4['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d4['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d4['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago5 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments_det(options, line_id, str('102.01.160'))
        if len(detPago5) > 0:
            lines.append({
                'id': '102.01.160',
                'name': 'MULTIVA 3879186 MN',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d5 in detPago5:

                subPago += d5['balance']
                subMxnPago += d5['balance']

                lines.append({
                    'id': '102.01.160',
                    'name': d5['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d5['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d5['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d5['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d5['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago6 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments_det(options, line_id, str('102.01.150'))
        if len(detPago6) > 0:
            lines.append({
                'id': '102.01.150',
                'name': 'BANBAJIO 0087999670201 MN',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d6 in detPago6:

                subPago += d6['balance']
                subMxnPago += d6['balance']

                lines.append({
                    'id': '102.01.150',
                    'name': d6['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d6['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d6['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d6['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d6['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago7 = self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(
            date_to))._paymentsext_det(options, line_id, str('102.01.350'))
        if len(detPago7) > 0:
            lines.append({
                'id': '102.01.350',
                'name': 'BANBAJIO 0087999671801 EURO',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d7 in detPago7:
                montomxn = 0
                if tipo_cambio_euro:
                    montomxn = d7['balance']*(1/tipo_cambio_euro.rate)
                else:
                    montomxn = d7['balance']*(1/1)

                subPago += d7['balance']
                subMxnPago += montomxn

                lines.append({
                    'id': '102.01.350',
                    'name': d7['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d7['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d7['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'EURO', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d7['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(montomxn)), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago8 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments_det(options, line_id, str('102.01.170'))
        if len(detPago8) > 0:
            lines.append({
                'id': '102.01.170',
                'name': 'BBASE 145691288080001018 MN',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d8 in detPago8:

                subPago += d8['balance']
                subMxnPago += d8['balance']

                lines.append({
                    'id': '102.01.170',
                    'name': d8['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d8['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d8['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d8['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d8['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago9 = self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(
            date_to))._paymentsext_det(options, line_id, str('102.01.270'))
        if len(detPago9) > 0:
            lines.append({
                'id': '102.01.270',
                'name': 'BBASE 145691288080002017 USD',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d9 in detPago9:
                montomxn = 0
                if tipo_cambio_usd:
                    montomxn = d9['balance']*(1/tipo_cambio_usd.rate)
                else:
                    montomxn = d9['balance']*(1/1)

                subPago += d9['balance']
                subMxnPago += montomxn

                lines.append({
                    'id': '102.01.270',
                    'name': d9['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d9['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d9['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'USD', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d9['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(montomxn)), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago10 = self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(
            date_to))._paymentsext_det(options, line_id, str('102.01.370'))
        if len(detPago10) > 0:
            lines.append({
                'id': '102.01.370',
                'name': 'BBASE 145691288080013019 EURO',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d10 in detPago10:
                montomxn = 0
                if tipo_cambio_euro:
                    montomxn = d10['balance']*(1/tipo_cambio_euro.rate)
                else:
                    montomxn = d10['balance']*(1/1)

                subPago += d10['balance']
                subMxnPago += montomxn

                lines.append({
                    'id': '102.01.350',
                    'name': d10['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d10['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d10['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'EURO', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d10['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(montomxn)), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago11 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments_det(options, line_id, str('103.01.001'))
        if len(detPago11) > 0:
            lines.append({
                'id': '103.01.001',
                'name': 'MULTIVA INTEGRA 6469507',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d11 in detPago11:

                subPago += d11['balance']
                subMxnPago += d11['balance']

                lines.append({
                    'id': '103.01.001',
                    'name': d11['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d11['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d11['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d11['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d11['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        detPago12 = self.with_context(date_from=fields.Date.from_string(
            date_from), date_to=fields.Date.from_string(date_to))._payments_det(options, line_id, str('103.01.002'))
        if len(detPago12) > 0:
            lines.append({
                'id': '103.01.002',
                'name': 'INVERSIÓN FONDO DE AHORRO',
                'level': 1,
                'class': 'cuentas',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                ],
            })

            for d12 in detPago12:

                subPago += d12['balance']
                subMxnPago += d12['balance']

                lines.append({
                    'id': '103.01.002',
                    'name': d12['tipo'],
                    'level': 2,
                    'class': 'cuentas',
                    'columns': [
                        {'name': d12['cliente'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': d12['etiqueta'][0:50],
                            'style': 'text-align: left; white-space:nowrap;'},
                        {'name': 'MXN', 'style': 'text-align: center; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d12['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                        {'name': self.format_value(
                            abs(d12['balance'])), 'style': 'text-align: right; white-space:nowrap;'},
                    ],
                })

        if abs(subPago) > 0:
            lines.append({
            'id': 'Subtotal',
            'name': '',
            'level': 1,
            'style': 'border-width: 3px;border-style: none none double none; font-size:15px;',
            'class': 'total',
            'columns': [
                {'name': ''},
                {'name': ''},
                {'name': 'SUBTOTAL:', 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    abs(subPago)), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': self.format_value(
                    abs(subMxnPago)), 'style': 'text-align: right; white-space:nowrap;'},
                {'name': ''},

            ],
        })

        # lines.append({
        # 'id': 'TOTAL MN DISP',
        # 'name': '',
        # 'level':1,
        # 'style': 'border-width: 3px;border-style: none none double none;',
        # 'class': 'total',
        # 'columns':[
        # {'name':''},
        # {'name':''},
        # {'name':''},
        # {'name':''},
        # {'name':''},
        # {'name':'TOTAL EN MXN + INV'},
        # {'name':self.format_value(total_mxn+balance_final10[0])},
        # ],
        # })

        return lines

    @api.model
    def _get_report_name(self):
        return _('Relación de Saldos Bancarios')
