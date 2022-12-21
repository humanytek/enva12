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


class ReportsBanks(models.AbstractModel):
    _name = "report.bank.nova"
    _description = "Reports Banks"
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}

    def _get_templates(self):
        templates = super(ReportsBanks, self)._get_templates()
        templates['line_template'] = 'reports_custom_bank.line_template_nova_banks'
        return templates

    def _get_columns_name(self, options):
        return [
        {'name': _(''), 'class': 'number', 'style': 'text-align: center; white-space:nowrap;'},
        {'name': _('SALDO INICIAL'), 'class': 'number', 'style': 'text-align: center; white-space:nowrap;'},
        {'name': _('CARGOS'), 'class': 'number', 'style': 'text-align: center; white-space:nowrap;'},
        {'name': _('ABONOS'), 'class': 'number', 'style':  'text-align: center; white-space:nowrap;'},
        {'name': _('INGRESOS'), 'class': 'number', 'style': 'text-align: center; white-space:nowrap;'},
        {'name': _('PAGOS CONTADO/CARTERA'), 'class': 'number', 'style': 'text-align: center; white-space:nowrap;'},
        {'name': _('SALDO DISPONIBLE'), 'class': 'number', 'style': 'text-align: center; white-space:nowrap;'},

        ]

    def _balance_initial(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+"""
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _payments(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is not Null )
                AND (rpc.name!='BANCO' OR rpc.name is Null)
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _transfer_in(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0

                AND (\"account_move_line\".partner_id is Null )
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _transfer_out(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is Null )
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _comision(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is not Null )
                AND rpc.name IN ('BANCO')
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _interes(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id is not Null )
                AND rpc.name IN ('BANCO')
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _transfer_inext(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0

                AND (\"account_move_line\".partner_id is Null )
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _transfer_outext(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is Null )
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _comisionext(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is not Null )
                AND rpc.name IN ('BANCO')
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _receivables(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id is not Null )
                AND rpc.name IN ('CORRUGADO','PAPEL')
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _devoluciones(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance

                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id is not Null )
                AND rp.id NOT IN (SELECT rp.id
                                FROM res_partner_category rpc
                                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.category_id=rpc.id
                                 WHERE rp.id=rpcr.partner_id AND rpc.name IN ('CORRUGADO','PAPEL') Limit 1)
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params


        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,0,)

        return result
    def _paymentsext(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit = 0 AND credit > 0
                AND (\"account_move_line\".partner_id is not Null )
                AND (rpc.name!='BANCO' OR rpc.name is Null)
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _receivablesext(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN res_partner rp on rp.id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=\"account_move_line\".partner_id
                LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                WHERE aa.code = %s """+where_clause+""" AND debit > 0 AND credit = 0
                AND (\"account_move_line\".partner_id is not Null )
                AND rpc.name IN ('CORRUGADO','PAPEL')
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result
    def _balance_initialext(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".amount_currency),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.code = %s """+where_clause+"""
                GROUP BY aa.id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        saldo_final_mxn=0
        saldo_final_usd=0
        saldo_final_euro=0
        pagos_mxn=0
        pagos_usd=0
        pagos_euro=0
        total_mxn=0
        total_usd=0
        total_euro=0
        balance_init4=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initialext(options,line_id,str('102.01.220'))
        balance_final4=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from))._balance_initialext(options,line_id,str('102.01.220'))
        pagos4=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._paymentsext(options,line_id,str('102.01.220'))
        ingresos4=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivablesext(options,line_id,str('102.01.220'))
        transfer_in4=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_inext(options,line_id,str('102.01.220'))
        transfer_out4=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_outext(options,line_id,str('102.01.220'))
        comision4=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comisionext(options,line_id,str('102.01.220'))
        lines.append({
        'id': '102.01.220',
        'name': 'BBVA BANCOMER 0100773034 USD',
        'level':2,
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init4[0]), 'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(comision4[0]+transfer_out4[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in4[0]), 'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos4[0]), 'style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init4[0]+ingresos4[0]+comision4[0]+transfer_out4[0]+transfer_in4[0])},
        {'name':self.format_value(abs(pagos4[0])), 'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final4[0]), 'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        saldo_final_usd+=balance_init4[0]+ingresos4[0]+comision4[0]+transfer_out4[0]+transfer_in4[0]
        pagos_usd+=pagos4[0]
        total_usd+=balance_final4[0]
        balance_init5=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initialext(options,line_id,str('102.01.320'))
        balance_final5=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from))._balance_initialext(options,line_id,str('102.01.320'))
        pagos5=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._paymentsext(options,line_id,str('102.01.320'))
        ingresos5=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivablesext(options,line_id,str('102.01.320'))
        transfer_in5=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_inext(options,line_id,str('102.01.320'))
        transfer_out5=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_outext(options,line_id,str('102.01.320'))
        comision5=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comisionext(options,line_id,str('102.01.320'))
        lines.append({
        'id': '102.01.320',
        'name': 'BBVA BANCOMER 0196249760 EURO',
        'level':2,
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init5[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(comision5[0]+transfer_out5[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in5[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos5[0]),'style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init5[0]+ingresos5[0]+comision5[0]+transfer_out5[0]+transfer_in5[0])},
        {'name':self.format_value(abs(pagos5[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final5[0]),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        saldo_final_euro+=balance_init5[0]+ingresos5[0]+comision5[0]+transfer_out5[0]+transfer_in5[0]
        pagos_euro+=pagos5[0]
        total_euro+=balance_final5[0]
        balance_init=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initial(options,line_id,str('102.01.120'))
        balance_final=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from))._balance_initial(options,line_id,str('102.01.120'))
        pagos=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._payments(options,line_id,str('102.01.120'))
        ingresos=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivables(options,line_id,str('102.01.120'))
        transfer_in=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options,line_id,str('102.01.120'))
        transfer_out=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options,line_id,str('102.01.120'))
        comision=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comision(options,line_id,str('102.01.120'))
        devoluciones=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._devoluciones(options,line_id,str('102.01.120'))
        lines.append({
        'id': '102.01.120',
        'name': 'BBVA BANCOMER 0132940590 MN',
        'level':2,
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init[0]),'style': 'text-align: right; white-space:nowrap;','style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(comision[0]+transfer_out[0])),'style': 'text-align: right; white-space:nowrap;','style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in[0]+devoluciones[0]),'style': 'text-align: right; white-space:nowrap;','style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos[0]),'style': 'text-align: right; white-space:nowrap;','style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init[0]+ingresos[0]+comision[0]+transfer_out[0]+transfer_in[0])},
        {'name':self.format_value(abs(pagos[0])),'style': 'text-align: right; white-space:nowrap;','style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final[0]),'style': 'text-align: right; white-space:nowrap;','style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        saldo_final_mxn+=balance_init[0]+ingresos[0]+comision[0]+transfer_out[0]+transfer_in[0]
        pagos_mxn+=pagos[0]
        total_mxn+=balance_final[0]
        balance_init1=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initial(options,line_id,str('102.01.140'))
        balance_final1=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) )._balance_initial(options,line_id,str('102.01.140'))
        pagos1=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._payments(options,line_id,str('102.01.140'))
        ingresos1=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivables(options,line_id,str('102.01.140'))
        devoluciones1=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._devoluciones(options,line_id,str('102.01.140'))
        transfer_in1=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options,line_id,str('102.01.140'))
        transfer_out1=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options,line_id,str('102.01.140'))
        comision1=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comision(options,line_id,str('102.01.140'))
        lines.append({
        'id': '102.01.140',
        'name': 'SANTANDER 65503315522 MN',
        'level':2,
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init1[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(transfer_out1[0]+comision1[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in1[0]+devoluciones1[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos1[0]),'style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init1[0]+ingresos1[0]+comision1[0]+transfer_out1[0]+transfer_in1[0])},
        {'name':self.format_value(abs(pagos1[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final1[0]),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        saldo_final_mxn+=balance_init1[0]+ingresos1[0]+comision1[0]+transfer_out1[0]+transfer_in1[0]
        pagos_mxn+=pagos1[0]
        total_mxn+=balance_final1[0]
        balance_init2=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initial(options,line_id,str('102.01.160'))
        balance_final2=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) )._balance_initial(options,line_id,str('102.01.160'))
        pagos2=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._payments(options,line_id,str('102.01.160'))
        ingresos2=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivables(options,line_id,str('102.01.160'))
        transfer_in2=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options,line_id,str('102.01.160'))
        transfer_out2=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options,line_id,str('102.01.160'))
        comision2=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comision(options,line_id,str('102.01.160'))
        devoluciones2=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._devoluciones(options,line_id,str('102.01.160'))

        lines.append({
        'id': '102.01.160',
        'name': 'MULTIVA 3879186 MN',
        'level':2,
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init2[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(transfer_out2[0]+comision2[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in2[0]+devoluciones2[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos2[0]),'style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init2[0]+ingresos2[0]+comision2[0]+transfer_out2[0]+transfer_in2[0])},
        {'name':self.format_value(abs(pagos2[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final2[0]),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        saldo_final_mxn+=balance_init2[0]+ingresos2[0]+comision2[0]+transfer_out2[0]+transfer_in2[0]
        pagos_mxn+=pagos2[0]
        total_mxn+=balance_final2[0]
        balance_init6=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initial(options,line_id,str('102.01.150'))
        balance_final6=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) )._balance_initial(options,line_id,str('102.01.150'))
        pagos6=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._payments(options,line_id,str('102.01.150'))
        ingresos6=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivables(options,line_id,str('102.01.150'))
        transfer_in6=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options,line_id,str('102.01.150'))
        transfer_out6=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options,line_id,str('102.01.150'))
        comision6=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comision(options,line_id,str('102.01.150'))
        lines.append({
        'id': '102.01.150',
        'name': 'BANBAJIO 0087999670201 MN',
        'level':2,
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init6[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(transfer_out6[0]+comision6[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in6[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos6[0]),'style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init6[0]+ingresos6[0]+comision6[0]+transfer_out6[0]+transfer_in6[0])},
        {'name':self.format_value(abs(pagos6[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final6[0]),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        saldo_final_mxn+=balance_init6[0]+ingresos6[0]+comision6[0]+transfer_out6[0]+transfer_in6[0]
        pagos_mxn+=pagos6[0]
        total_mxn+=balance_final6[0]
        balance_init7=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initialext(options,line_id,str('102.01.350'))
        balance_final7=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) )._balance_initialext(options,line_id,str('102.01.350'))
        pagos7=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._paymentsext(options,line_id,str('102.01.350'))
        ingresos7=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivablesext(options,line_id,str('102.01.350'))
        transfer_in7=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_inext(options,line_id,str('102.01.350'))
        transfer_out7=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_outext(options,line_id,str('102.01.350'))
        comision7=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comisionext(options,line_id,str('102.01.350'))
        lines.append({
        'id': '102.01.350',
        'name': 'BANBAJIO 0087999671801 EURO',
        'level':2,
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init7[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(transfer_out7[0]+comision7[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in7[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos7[0]),'style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init7[0]+ingresos7[0]+comision7[0]+transfer_out7[0]+transfer_in7[0])},
        {'name':self.format_value(abs(pagos7[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final7[0]),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        saldo_final_euro+=balance_init7[0]+ingresos7[0]+comision7[0]+transfer_out7[0]+transfer_in7[0]
        pagos_euro+=pagos7[0]
        total_euro+=balance_final7[0]
        balance_init8=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initial(options,line_id,str('102.01.170'))
        balance_final8=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) )._balance_initial(options,line_id,str('102.01.170'))
        pagos8=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._payments(options,line_id,str('102.01.170'))
        ingresos8=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivables(options,line_id,str('102.01.170'))
        transfer_in8=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options,line_id,str('102.01.170'))
        transfer_out8=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options,line_id,str('102.01.170'))
        comision8=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comision(options,line_id,str('102.01.170'))
        lines.append({
        'id': '102.01.170',
        'name': 'BBASE 145691288080001018 MN',
        'level':2,
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init8[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(transfer_out8[0]+comision8[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in8[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos8[0]),'style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init8[0]+ingresos8[0]+comision8[0]+transfer_out8[0]+transfer_in8[0])},
        {'name':self.format_value(abs(pagos8[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final8[0]),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        saldo_final_mxn+=balance_init8[0]+ingresos8[0]+comision8[0]+transfer_out8[0]+transfer_in8[0]
        pagos_mxn+=pagos8[0]
        total_mxn+=balance_final8[0]
        balance_init3=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initialext(options,line_id,str('102.01.270'))
        balance_final3=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) )._balance_initialext(options,line_id,str('102.01.270'))
        pagos3=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._paymentsext(options,line_id,str('102.01.270'))
        ingresos3=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivablesext(options,line_id,str('102.01.270'))
        transfer_in3=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_inext(options,line_id,str('102.01.270'))
        transfer_out3=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_outext(options,line_id,str('102.01.270'))
        comision3=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comisionext(options,line_id,str('102.01.270'))
        lines.append({
        'id': '102.01.270',
        'name': 'BBASE 145691288080002017 USD',
        'level':2,
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init3[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(transfer_out3[0]+comision3[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in3[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos3[0]),'style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init3[0]+ingresos3[0]+comision3[0]+transfer_out3[0]+transfer_in3[0])},
        {'name':self.format_value(abs(pagos3[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final3[0]),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        saldo_final_usd+=balance_init3[0]+ingresos3[0]+comision3[0]+transfer_out3[0]+transfer_in3[0]
        pagos_usd+=pagos3[0]
        total_usd+=balance_final3[0]
        balance_init9=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initialext(options,line_id,str('102.01.370'))
        balance_final9=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) )._balance_initialext(options,line_id,str('102.01.370'))
        pagos9=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._paymentsext(options,line_id,str('102.01.370'))
        ingresos9=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivablesext(options,line_id,str('102.01.370'))
        transfer_in9=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_inext(options,line_id,str('102.01.370'))
        transfer_out9=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_outext(options,line_id,str('102.01.370'))
        comision9=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comisionext(options,line_id,str('102.01.370'))
        lines.append({
        'id': '102.01.270',
        'name': 'BBASE 145691288080013019 EURO',
        'level':2,
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init9[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(transfer_out9[0]+comision9[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in9[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos9[0]),'style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init9[0]+ingresos9[0]+comision9[0]+transfer_out9[0]+transfer_in9[0])},
        {'name':self.format_value(abs(pagos9[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final9[0]),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        saldo_final_euro+=balance_init9[0]+ingresos9[0]+comision9[0]+transfer_out9[0]+transfer_in9[0]
        pagos_euro+=pagos9[0]
        total_euro+=balance_final9[0]
        balance_init10=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initial(options,line_id,str('103.01.001'))
        balance_final10=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) )._balance_initial(options,line_id,str('103.01.001'))
        pagos10=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._payments(options,line_id,str('103.01.001'))
        ingresos10=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._receivables(options,line_id,str('103.01.001'))
        transfer_in10=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_in(options,line_id,str('103.01.001'))
        transfer_out10=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._transfer_out(options,line_id,str('103.01.001'))
        comision10=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._comision(options,line_id,str('103.01.001'))
        interes10=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._interes(options,line_id,str('103.01.001'))
        lines.append({
        'id': '103.01.001',
        'name': 'MULTIVA INTEGRA  6469507',
        'level':0,
        'style': 'border-style: none;',
        'class': 'cuentas',
        'columns':[
        {'name':self.format_value(balance_init10[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(abs(transfer_out10[0]+comision10[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(transfer_in10[0]+interes10[0]),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(ingresos10[0]),'style': 'text-align: right; white-space:nowrap;'},
        # {'name':self.format_value(balance_init10[0]+ingresos10[0]+comision10[0]+transfer_out10[0]+transfer_in10[0])},
        {'name':self.format_value(abs(pagos10[0])),'style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(balance_final10[0]),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })

        lines.append({
        'id': 'TOTAL',
        'name': '',
        'level':0,
        'class': 'total',
        'columns':[
        {'name':''},
        {'name':''},
        {'name':''},
        {'name':''},
        {'name':''},
        {'name':''},
        # {'name':''},
        ],
        })
        lines.append({
        'id': 'TOTAL MN',
        'name': '',
        'level':1,
        'style': 'border-style: none;',
        'class': 'total',
        'columns':[
        {'name':''},
        {'name':''},
        {'name':''},
        {'name':''},
        # {'name':self.format_value(saldo_final_mxn)},
        # {'name':self.format_value(abs(pagos_mxn))},
        {'name':'TOTAL M.N.:','style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(total_mxn),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })

        lines.append({
        'id': 'TOTAL USD',
        'name': '',
        'level':1,
        'style': 'border-style: none;',
        'class': 'total',
        'columns':[
        {'name':''},
        {'name':''},
        {'name':''},
        {'name':''},
        # {'name':self.format_value(saldo_final_usd)},
        # {'name':self.format_value(abs(pagos_usd))},
        {'name':'TOTAL USD:','style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(total_usd),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        tipo_cambio_usd=self.env['res.currency.rate'].search(['&',('currency_id','=',2),('name','=',fields.Date.from_string(date_from))])
        tipo_cambio_euro=self.env['res.currency.rate'].search(['&',('currency_id','=',1),('name','=',fields.Date.from_string(date_from))])
        if tipo_cambio_usd:
            total_usd_to_mxn=total_usd*(1/tipo_cambio_usd.rate)
        else:
            total_usd_to_mxn=total_usd*(1/1)
        lines.append({
        'id': 'TOTAL EURO',
        'name': '',
        'level':1,
        'style': 'border-width: 3px;border-style: none none double none;',
        'class': 'total',
        'columns':[
        {'name':''},
        {'name':''},

        {'name':''},
        {'name':''},
        # {'name':self.format_value(saldo_final_euro)},
        # {'name':self.format_value(abs(pagos_euro))},
        {'name':'TOTAL EURO:','style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(total_euro),'style': 'text-align: right; white-space:nowrap;'},
        ],
        })
        if tipo_cambio_euro:
            total_euro_to_mxn=total_euro*(1/tipo_cambio_euro.rate)
        else:
            total_euro_to_mxn=total_euro*(1/1)
        lines.append({
        'id': 'TOTAL MN DISP',
        'name': '',
        'level':1,
        'style': 'border-width: 3px;border-style: none none double none; font-size:15px;',
        'class': 'total',
        'columns':[
        {'name':''},
        {'name':''},
        {'name':''},
        {'name':''},
        {'name':'TOTAL EN M.N. DISP:','style': 'text-align: right; white-space:nowrap;'},
        {'name':self.format_value(total_mxn+balance_final10[0]+total_usd_to_mxn+total_euro_to_mxn),'style': 'text-align: right; white-space:nowrap;'},
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
