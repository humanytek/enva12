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

class ReportsAccount(models.AbstractModel):
    _name = "report.account.nova"
    _description = "Reports Account"
    _inherit = 'account.report'

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_all_entries = False

    def _get_columns_name(self, options):
        return [{'name': ''}, {'name': _('ESTE MES'), 'class': 'number', 'style': 'white-space:nowrap;'}, {'name': _('MES ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},{'name': _('DIC EJ. ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'}]

    def _balance_initial(self,options,line_id,arg):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                WHERE aa.group_finantial_id = %s """+where_clause+"""
                GROUP BY aa.group_finantial_id
        """
        params = [str(arg)] + where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result

    def _balance_initial_earning(self,options,line_id):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause

        sql_query ="""
            SELECT COALESCE(SUM(\"account_move_line\".balance),0) as balance
                FROM """+tables+"""
                LEFT JOIN account_account aa on aa.id=\"account_move_line\".account_id
                LEFT JOIN account_account_type aat on aat.id=aa.internal_type
                WHERE aat.include_initial_balance = False AND """+where_clause+"""
                GROUP BY aat.include_initial_balance
        """
        params = where_params

        self.env.cr.execute(sql_query, params)
        result = self.env.cr.fetchone()
        if result==None:
            result=(0,)

        return result

    def _calculate_formula(self,options,line_id,formula,mes,date_from,date_to):
        mews=0
        totalm=""
        groups_month = mes
        newvalue = []
        datos = formula.split()
        for d in datos:
            if d=="(" or d==")" or d=="-" or d=="+" or d=="*" or d=="/":
                newvalue.append(d)
            else:
                if d.isnumeric():
                    newvalue.append(d)
                else:
                    form=d.split("#")
                    if form[0]=="C":
                        newvalue.append(groups_month.get(form[1],0))
                    elif form[0]=="G":
                        group=self.env['account.group.nova'].search([('code_prefix','=',form[1])],order='code_prefix')
                        if group:
                            balance=self.with_context(date_from=date_from, date_to=date_to)._balance_initial(options,line_id,str(group.id))
                            if balance:
                                newvalue.append(balance[0])

        for n in newvalue:
            totalm+=str(n)
        try:
            mews=eval(totalm)
        except ZeroDivisionError as err:
            if 'division by zero' in err.args[0]:
                mews = 0
            else:
                raise err
        return mews


    def _calculate_formulab(self,options,line_id,formula,mes,date_from,date_to):
        mews=0
        totalm=""
        groups_month = mes
        newvalue = []
        datos = formula.split()
        for d in datos:
            if d=="(" or d==")" or d=="-" or d=="+" or d=="*" or d=="/":
                newvalue.append(d)
            else:
                if d.isnumeric():
                    newvalue.append(d)
                else:
                    form=d.split("#")
                    if form[0]=="C":
                        newvalue.append(groups_month.get(form[1],0))
                    elif form[0]=="G":
                        group=self.env['account.group.nova'].search([('code_prefix','=',form[1])],order='code_prefix')

                        if group:
                            balance=self.with_context(date_from=date_from, date_to=date_to)._balance_initial(options,line_id,str(group.id))
                            balance_init=self.with_context(date_from=False, date_to=date_from + timedelta(days=-1))._balance_initial(options,line_id,str(group.id))
                            if balance:
                                if balance_init:
                                    newvalue.append(balance[0]+balance_init[0])
                                else:
                                    newvalue.append(balance[0])

        for n in newvalue:
            totalm+=str(n)
        try:
            mews=eval(totalm)
        except ZeroDivisionError as err:
            if 'division by zero' in err.args[0]:
                mews = 0
            else:
                raise err
        return mews


    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        groups_month = {}

        groups_prev_month = {}
        groups_dec_prev_year = {}
        signo = 1
        valor = 0
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        last_day_previous_fy = self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'] + timedelta(days=-1)
        group=self.env['reports.group'].search([('type','in',['BALANCE GENERAL'])],order='order')
        if group:
            for g in group:
                if g.negative:
                    signo=-1
                if g.formula==False:


                    if g.title:
                        lines.append({
                        'id': g.id,
                        'name': g.name,
                        'level': g.level,
                        'class': 'activo',
                        'columns':[{'name':''},{'name':''},{'name':''}],
                        })
                    elif g.type_balance=="RESULTADO EJ. ANT" and g.group_finantial_id.id:
                        if g.acum_invisible and g.title==False:
                            date_to_prev=fields.Date.from_string(date_from)

                            balance_init=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from)+ timedelta(days=-1))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            balance=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            balance_ejer_ant=self.with_context(date_from=False, date_to=last_day_previous_fy)._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            balance_init_earning_month=self.with_context(date_from=False, date_to=last_day_previous_fy)._balance_initial_earning(options,line_id)
                            if date_to_prev.month == 1:
                                balance_init_earning=self.with_context(date_from=False, date_to=last_day_previous_fy+relativedelta(years=-1))._balance_initial_earning(options,line_id)
                            else:
                                balance_init_earning=self.with_context(date_from=False, date_to=last_day_previous_fy)._balance_initial_earning(options,line_id)

                            balance_init_earning_ant=self.with_context(date_from=False, date_to=last_day_previous_fy+relativedelta(years=-1))._balance_initial_earning(options,line_id)
                            if balance_init and balance_init_earning:
                                groups_prev_month[g.code]=balance_init[0]+balance_init_earning[0]
                            else:
                                groups_prev_month[g.code]=balance_init_earning[0]
                            if balance and balance_init and balance_init_earning :
                                groups_month[g.code]=balance[0]+balance_init[0]+balance_init_earning_month[0]
                            else:
                                groups_month[g.code]=balance_init[0]+balance_init_earning_month[0]
                            if balance_ejer_ant and balance_init_earning_ant:
                                groups_dec_prev_year[g.code]=balance_ejer_ant[0]+balance_init_earning_ant[0]
                            else:
                                groups_dec_prev_year[g.code]=balance_init_earning_ant[0]
                        else:
                            date_to_prev=fields.Date.from_string(date_from)

                            balance_init=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            balance=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            balance_ejer_ant=self.with_context(date_from=False, date_to=last_day_previous_fy)._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            balance_init_earning_month=self.with_context(date_from=False, date_to=last_day_previous_fy)._balance_initial_earning(options,line_id)
                            if date_to_prev.month == 1:
                                balance_init_earning=self.with_context(date_from=False, date_to=last_day_previous_fy+relativedelta(years=-1))._balance_initial_earning(options,line_id)
                            else:
                                balance_init_earning=self.with_context(date_from=False, date_to=last_day_previous_fy)._balance_initial_earning(options,line_id)

                            balance_init_earning_ant=self.with_context(date_from=False, date_to=last_day_previous_fy+relativedelta(years=-1))._balance_initial_earning(options,line_id)
                            if balance_init and balance_init_earning:
                                groups_prev_month[g.code]=balance_init[0]+balance_init_earning[0]
                            else:
                                groups_prev_month[g.code]=balance_init_earning[0]
                            if balance and balance_init and balance_init_earning :
                                groups_month[g.code]=balance[0]+balance_init[0]+balance_init_earning_month[0]
                            else:
                                groups_month[g.code]=balance_init[0]+balance_init_earning_month[0]
                            if balance_ejer_ant and balance_init_earning_ant:
                                groups_dec_prev_year[g.code]=balance_ejer_ant[0]+balance_init_earning_ant[0]
                            else:
                                groups_dec_prev_year[g.code]=balance_init_earning_ant[0]
                            lines.append({
                            'id': g.id,
                            'name': g.name,
                            'level': g.level,
                            'class': 'activo',
                            'columns':[
                            {'name':self.format_value(groups_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'}
                            ],
                            })

                    elif g.type_balance=="RESULTADO DEL EJERCICIO" and g.group_finantial_id.id==False:
                        if g.acum_invisible and g.title==False:
                            date_to_prev=fields.Date.from_string(date_from)
                            balance_init_earning=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))._balance_initial_earning(options,line_id)
                            if date_to_prev.month == 1:
                                balance_init_earning_prev_month=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=fields.Date.from_string(date_from)+timedelta(days=-1))._balance_initial_earning(options,line_id)
                            else:
                                balance_init_earning_prev_month=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_from)+timedelta(days=-1))._balance_initial_earning(options,line_id)

                            balance_init_earning_prev_year=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+timedelta(days=-1))._balance_initial_earning(options,line_id)

                            if balance_init_earning:
                                groups_month[g.code]=balance_init_earning[0]
                            if balance_init_earning_prev_month:
                                groups_prev_month[g.code]=balance_init_earning_prev_month[0]
                            if balance_init_earning_prev_year:
                                groups_dec_prev_year[g.code]=balance_init_earning_prev_year[0]
                        else:

                            date_to_prev=fields.Date.from_string(date_from)
                            balance_init_earning=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))._balance_initial_earning(options,line_id)
                            if date_to_prev.month == 1:
                                balance_init_earning_prev_month=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=fields.Date.from_string(date_from)+timedelta(days=-1))._balance_initial_earning(options,line_id)
                            else:
                                balance_init_earning_prev_month=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_from)+timedelta(days=-1))._balance_initial_earning(options,line_id)

                            balance_init_earning_prev_year=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+timedelta(days=-1))._balance_initial_earning(options,line_id)

                            if balance_init_earning:
                                groups_month[g.code]=balance_init_earning[0]
                            if balance_init_earning_prev_month:
                                groups_prev_month[g.code]=balance_init_earning_prev_month[0]
                            if balance_init_earning_prev_year:
                                groups_dec_prev_year[g.code]=balance_init_earning_prev_year[0]
                            lines.append({
                            'id': g.id,
                            'name': g.name,
                            'level': g.level,
                            'class': 'activo',
                            'columns':[
                            {'name':self.format_value(groups_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'}
                            ],
                            })

                    else:
                        if g.acum_invisible and g.title==False:
                            balance_init=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from)+ timedelta(days=-1))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            balance=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            balance_ejer_ant=self.with_context(date_from=False, date_to=last_day_previous_fy)._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            if balance_init:
                                groups_prev_month[g.code]=balance_init[0]
                            if balance:
                                groups_month[g.code]=balance[0]+balance_init[0]
                            if balance_ejer_ant:
                                groups_dec_prev_year[g.code]=balance_ejer_ant[0]
                        else:
                            balance_init=self.with_context(date_from=False, date_to=fields.Date.from_string(date_from)+ timedelta(days=-1))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            balance=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            balance_ejer_ant=self.with_context(date_from=False, date_to=last_day_previous_fy)._balance_initial(options,line_id,str(g.group_finantial_id.id))
                            if balance_init:
                                groups_prev_month[g.code]=balance_init[0]
                            if balance:
                                groups_month[g.code]=balance[0]+balance_init[0]
                            if balance_ejer_ant:
                                groups_dec_prev_year[g.code]=balance_ejer_ant[0]
                            lines.append({
                            'id': g.id,
                            'name': g.name,
                            'level': g.level,
                            'class': 'activo',
                            'columns':[
                            {'name':self.format_value(groups_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'}
                            ],
                            })
                else:

                    if g.expresion:
                        mes=self._calculate_formulab(options,line_id,g.expresion,groups_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                        mes_anterior=self._calculate_formula(options,line_id,g.expresion,groups_prev_month,date_from=False, date_to=fields.Date.from_string(date_from)+ timedelta(days=-1))
                        año_anterior=self._calculate_formula(options,line_id,g.expresion,groups_dec_prev_year,date_from=False, date_to=last_day_previous_fy)
                        if mes:
                            groups_month[g.code]=mes
                        if mes_anterior:
                            groups_prev_month[g.code]=mes_anterior
                        if año_anterior:
                            groups_dec_prev_year[g.code]=año_anterior

                    if g.title:
                        lines.append({
                        'id': g.id,
                        'name': g.name,
                        'level': g.level,
                        'class': 'activo',
                        'columns':[{'name':''},{'name':''},{'name':''}],
                        })
                    elif g.acum_invisible and g.title==False:
                        pass
                    else:
                        lines.append({
                        'id': g.id,
                        'name': g.name,
                        'level': g.level,
                        'class': 'activo',
                        'columns':[
                        {'name':self.format_value(groups_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number' },
                        {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number' },
                        {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number' }] ,
                        })




        # _logger.info('imprimir conceptos ---- %s', conceptos)




        return lines

    @api.model
    def _get_report_name(self):
        return _('Balance General')
