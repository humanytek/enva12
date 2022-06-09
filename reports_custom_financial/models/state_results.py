# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import time
from odoo import api, models,fields, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.addons.web.controllers.main import clean_action
_logger = logging.getLogger(__name__)

class ReportStateResults(models.AbstractModel):
    _name = "report.state.results.nova"
    _description = "Estado de Resultados Empaquesnova"
    _inherit = 'report.account.nova'

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_all_entries = False


    # def _get_templates(self):
    #     templates = super(ReportStateResults, self)._get_templates()
    #     templates['main_table_header_template'] = 'reports_custom_financial.template_state_result_table_header'
    #     return templates

    def _get_columns(self, options):

        header1 = [
            {'name': '', 'style': 'width:40%'},
            {'name': _('MES'),'class': 'number', 'colspan': 8},
            {'name': _('ACUMULADO'),'class': 'number', 'colspan': 6},
        ]
        header2 = [ {'name': '', 'style': 'width:40%'},
                    {'name': _('REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
                    {'name': ''},
                    {'name': _('ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},
                    {'name': ''},
                    {'name': _('PRESUPUESTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
                    {'name': ''},
                    {'name': _('AÑO ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},
                    {'name': ''},
                    {'name': _('REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
                    {'name': ''},
                    {'name': _('PRESUPUESTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
                    {'name': ''},
                    {'name': _('ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},
                    {'name': ''}
                    ]
        return [header1,header2]

    def _get_cost_sales(self, ncost, date_f,date_t):
        porcentaje=self.env['porcent.cost.sale'].search(['&','&',('name','=',ncost),('date_from','>=',date_f),('date_to','<=',date_t)])
        porcentajeacum=0
        if porcentaje:
            for p in porcentaje:
                porcentajeacum+=p.porcent_per_month
        else:
            porcentajeacum=0

        return porcentajeacum

    def _get_volumen_sale_boxpaper(self,nvolumen,date_f,date_t,budget):
        volumen=self.env['volumen.sales'].search(['&','&',('name','=',nvolumen),('date_from','>=',date_f),('date_to','<=',date_t)])
        volumenacum=0
        if budget:
            if volumen:
                for v in volumen:
                    volumenacum+=v.ton_per_month_budget
        else:
            if volumen:
                for v in volumen:
                    volumenacum+=v.ton_per_month

        return volumenacum

    def _get_budget_statement(self, nstate, date_f,date_t):
        budget=self.env['budget.statement.income'].search(['&','&',('name','=',nstate),('date_from','>=',date_f),('date_to','<=',date_t)])
        budgetacum=0
        if budget:
            for b in budget:
                budgetacum+=b.amount_per_month

        return budgetacum

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        groups_real = {}
        groups_real_porc = {}

        groups_prev_month = {}
        groups_prev_month_porc = {}

        groups_dec_prev_year = {}
        groups_dec_prev_year_porc = {}

        groups_acum = {}
        groups_acum_porc = {}

        groups_acum_month = {}
        groups_acum_month_porc = {}

        groups_budget_month = {}
        groups_budget_month_porc = {}

        groups_budget_month_ly = {}
        groups_budget_month_ly_porc = {}

        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        last_day_previous_fy = self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'] + timedelta(days=-1)
        group=self.env['reports.group'].search([('type','in',['ESTADO DE RESULTADOS'])],order='order')
        if group:
            for g in group:

                #SELECCION DE TITULOS
                if g.title or g.titulo_porcent:
                    if g.titulo_porcent==False:
                        lines.append({
                                'id': g.id,
                                'name': g.name,
                                'level': g.level,
                                'class': 'activo',
                                'columns':[
                                {'name':''},
                                {'name': ''},
                                {'name':''},
                                {'name': ''},
                                {'name':''},
                                {'name': ''},
                                {'name':''},
                                {'name': ''},
                                {'name':''},
                                {'name': ''},
                                {'name':''},
                                {'name': ''},
                                {'name':''},
                                {'name': ''}
                                ],
                                })
                    else:
                        lines.append({
                                'id': g.id,
                                'name': g.name,
                                'level': g.level,
                                'class': 'activo',
                                'columns':[
                                {'name':''},
                                {'name': '%','class': 'number', 'style': 'white-space:nowrap;'},
                                {'name':''},
                                {'name': '%','class': 'number', 'style': 'white-space:nowrap;'},
                                {'name':''},
                                {'name': '%','class': 'number', 'style': 'white-space:nowrap;'},
                                {'name':''},
                                {'name': '%','class': 'number', 'style': 'white-space:nowrap;'},
                                {'name':''},
                                {'name': '%','class': 'number', 'style': 'white-space:nowrap;'},
                                {'name':''},
                                {'name': '%','class': 'number', 'style': 'white-space:nowrap;'},
                                {'name':''},
                                {'name': '%','class': 'number', 'style': 'white-space:nowrap;'}
                                ],
                                })
                #SELECCION DE GRUPOS
                elif g.has_a_group:
                    signo = 1
                    if g.negative:
                        signo=-1

                    if g.group_finantial_id:

                        balance=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to) )._balance_initial(options,line_id,str(g.group_finantial_id.id))
                        balance_prev_month=self.with_context(date_from=fields.Date.from_string(date_from)+relativedelta(months=-1), date_to=fields.Date.from_string(date_from)+timedelta(days=-1) )._balance_initial(options,line_id,str(g.group_finantial_id.id))
                        balance_prev_year=self.with_context(date_from=fields.Date.from_string(date_from)+relativedelta(years=-1), date_to=fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1) )._balance_initial(options,line_id,str(g.group_finantial_id.id))
                        balance_acumulado=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                        balance_acumulado_month=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                        if balance:
                            groups_real[g.code]=balance[0]
                        if balance_prev_month:
                            groups_prev_month[g.code]=balance_prev_month[0]
                        if balance_prev_year:
                            groups_dec_prev_year[g.code]=balance_prev_year[0]
                        if balance_acumulado:
                            groups_acum[g.code]=balance_acumulado[0]
                        if balance_acumulado_month:
                            groups_acum_month[g.code]=balance_acumulado_month[0]

                        if g.budget_nova_id:
                            budget_month=self._get_budget_statement(g.budget_nova_id.id,fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                            budget_month_ly=self._get_budget_statement(g.budget_nova_id.id,self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to))
                            if budget_month:
                                groups_budget_month[g.code]=budget_month
                            if budget_month_ly:
                                groups_budget_month_ly[g.code]=budget_month_ly

                        if g.formula_porcent:
                            calmesporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_real,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                            calmesprevporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_prev_month,date_from=fields.Date.from_string(date_from)+relativedelta(months=-1), date_to=fields.Date.from_string(date_from)+timedelta(days=-1))
                            calbudgetmesporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_budget_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                            caldec_prev_yearporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_dec_prev_year,date_from=fields.Date.from_string(date_from)+relativedelta(years=-1), date_to = fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1))
                            calgroups_acumporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_acum,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))
                            calbudget_month_lyporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_budget_month_ly,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))
                            calacum_monthporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_acum_month,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1))
                            if calmesporc:
                                groups_real_porc[g.code]=calmesporc
                            if calmesprevporc:
                                groups_prev_month_porc[g.code]=calmesprevporc
                            if calbudgetmesporc:
                                groups_budget_month_porc[g.code]=calbudgetmesporc
                            if caldec_prev_yearporc:
                                groups_dec_prev_year_porc[g.code]=caldec_prev_yearporc
                            if calgroups_acumporc:
                                groups_acum_porc[g.code]=calgroups_acumporc
                            if calbudget_month_lyporc:
                                groups_budget_month_ly_porc[g.code]=calbudget_month_lyporc
                            if calacum_monthporc:
                                groups_acum_month_porc[g.code]=calacum_monthporc
                    if g.acum_invisible:
                        pass
                    else:


                        if g.formula_porcent:
                            lines.append({
                            'id': g.id,
                            'name':g.name,
                            'level': g.level,
                            'class': 'activo',
                            'columns':[
                            {'name':self.format_value(groups_real.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name':'' if g.formula_porcent==False else "{:.2%}".format(groups_real_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_prev_month_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name':'' if g.has_a_budget==False else self.format_value(groups_budget_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name':'' if g.has_a_budget==False or g.formula_porcent==False else "{:.2%}".format(groups_budget_month_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': '' if g.formula_porcent==False else  "{:.2%}".format(groups_dec_prev_year_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name':self.format_value(groups_acum.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_acum_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name': '' if g.has_a_budget==False else self.format_value(groups_budget_month_ly.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': '' if g.has_a_budget==False or g.formula_porcent==False else "{:.2%}".format(groups_budget_month_ly_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name':self.format_value(groups_acum_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_acum_month_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'}],
                            })
                        else:
                            lines.append({
                            'id': g.id,
                            'name':g.name,
                            'level': g.level,
                            'class': 'activo',
                            'columns':[
                            {'name':self.format_value(groups_real.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name':'' if g.has_a_budget==False else self.format_value(groups_budget_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name':self.format_value(groups_acum.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name': '' if g.has_a_budget==False else self.format_value(groups_budget_month_ly.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name':self.format_value(groups_acum_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''}],
                            })



                #SELECCION SI ES FORMULA
                elif g.formula:
                    signo = 1
                    if g.negative:
                        signo=-1


                    mesreal=0
                    mesanterior=0
                    mespresupuesto=0
                    anioanterior=0
                    realacumulado=0
                    presupuestoacumulado=0
                    acumuladoañoanterior=0
                    if g.expresion:

                        mesreal=self._calculate_formula(options,line_id,g.expresion,groups_real,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                        mesanterior=self._calculate_formula(options,line_id,g.expresion,groups_prev_month,date_from=fields.Date.from_string(date_from)+relativedelta(months=-1), date_to=fields.Date.from_string(date_from)+timedelta(days=-1))
                        mespresupuesto=self._calculate_formula(options,line_id,g.expresion,groups_budget_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                        anioanterior=self._calculate_formula(options,line_id,g.expresion,groups_dec_prev_year,date_from=fields.Date.from_string(date_from)+relativedelta(years=-1), date_to=fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1))
                        realacumulado=self._calculate_formula(options,line_id,g.expresion,groups_acum,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))
                        presupuestoacumulado=self._calculate_formula(options,line_id,g.expresion,groups_budget_month_ly,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))
                        acumuladoanioanterior=self._calculate_formula(options,line_id,g.expresion,groups_acum_month,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1))
                        if mesreal:
                            groups_real[g.code]=mesreal
                        if mesanterior:
                            groups_prev_month[g.code]=mesanterior
                        if mespresupuesto:
                            groups_budget_month[g.code]=mespresupuesto
                        if anioanterior:
                            groups_dec_prev_year[g.code]=anioanterior
                        if realacumulado:
                            groups_acum[g.code]=realacumulado
                        if presupuestoacumulado:
                            groups_budget_month_ly[g.code]=presupuestoacumulado
                        if acumuladoanioanterior:
                            groups_acum_month[g.code]=acumuladoanioanterior
                        if g.formula_porcent:
                            calmesporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_real,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                            calmesprevporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_prev_month,date_from=fields.Date.from_string(date_from)+relativedelta(months=-1), date_to=fields.Date.from_string(date_from)+timedelta(days=-1))
                            calbudgetmesporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_budget_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                            caldec_prev_yearporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_dec_prev_year,date_from=fields.Date.from_string(date_from)+relativedelta(years=-1), date_to = fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1))
                            calgroups_acumporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_acum,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))
                            calbudget_month_lyporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_budget_month_ly,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))
                            calacum_monthporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_acum_month,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1))
                            if calmesporc:
                                groups_real_porc[g.code]=calmesporc
                            if calmesprevporc:
                                groups_prev_month_porc[g.code]=calmesprevporc
                            if calbudgetmesporc:
                                groups_budget_month_porc[g.code]=calbudgetmesporc
                            if caldec_prev_yearporc:
                                groups_dec_prev_year_porc[g.code]=caldec_prev_yearporc
                            if calgroups_acumporc:
                                groups_acum_porc[g.code]=calgroups_acumporc
                            if calbudget_month_lyporc:
                                groups_budget_month_ly_porc[g.code]=calbudget_month_lyporc
                            if calacum_monthporc:
                                groups_acum_month_porc[g.code]=calacum_monthporc

                    if g.acum_invisible:
                        pass
                    else:
                        if g.formula_porcent:

                            lines.append({
                            'id': g.id,
                            'name':g.name,
                            'level': g.level,
                            'class': 'activo',
                            'columns':[
                            {'name':self.format_value(groups_real.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name':'' if g.formula_porcent==False else "{:.2%}".format(groups_real_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_prev_month_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name':'' if g.has_a_budget==False else self.format_value(groups_budget_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name':'' if g.has_a_budget==False or g.formula_porcent==False else "{:.2%}".format(groups_budget_month_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': '' if g.formula_porcent==False else  "{:.2%}".format(groups_dec_prev_year_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name':self.format_value(groups_acum.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_acum_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name': '' if g.has_a_budget==False else self.format_value(groups_budget_month_ly.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': '' if g.has_a_budget==False or g.formula_porcent==False else "{:.2%}".format(groups_budget_month_ly_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                            {'name':self.format_value(groups_acum_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_acum_month_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'}],
                            })
                        else:
                            lines.append({
                            'id': g.id,
                            'name':g.name,
                            'level': g.level,
                            'class': 'activo',
                            'columns':[
                            {'name':self.format_value(groups_real.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name':'' if g.has_a_budget==False else self.format_value(groups_budget_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name':self.format_value(groups_acum.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name': '' if g.has_a_budget==False else self.format_value(groups_budget_month_ly.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''},
                            {'name':self.format_value(groups_acum_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                            {'name': ''}],
                            })
                elif g.caculate_especial_cventa:
                    signo = 1
                    if g.negative:
                        signo=-1

                    porcentaje=self.env['porcent.cost.sale'].search(['&','&',('name','=',g.costo_venta_id.id),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_to))])
                    porcent_prev_month=self.env['porcent.cost.sale'].search(['&','&',('name','=',g.costo_venta_id.id),('date_from','>=',fields.Date.from_string(date_from)+relativedelta(months=-1)),('date_to','<=',fields.Date.from_string(date_from)+timedelta(days=-1))])
                    porcent_prev_year=self.env['porcent.cost.sale'].search(['&','&',('name','=',g.costo_venta_id.id),('date_from','>=',fields.Date.from_string(date_from)+relativedelta(years=-1)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1))])
                    # _logger.info('fecha año ---- %s', fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1))
                    porcent_acumulado=self._get_cost_sales(g.costo_venta_id.id,self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to))
                    porcent_acumulado_prevyear=self._get_cost_sales(g.costo_venta_id.id,self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1),fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1))
                    if g.budget_nova_id:
                        budget_month=self._get_budget_statement(g.budget_nova_id.id,fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                        budget_month_ly=self._get_budget_statement(g.budget_nova_id.id,self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to))
                        if budget_month:
                            groups_budget_month[g.code]=budget_month

                        if budget_month_ly:
                            groups_budget_month_ly[g.code]=budget_month_ly


                    if porcentaje:
                        groups_real[g.code]=porcentaje.porcent_per_month
                    else:
                        groups_real[g.code]=0
                    if porcent_prev_month:
                        groups_prev_month[g.code]=porcent_prev_month.porcent_per_month
                    else:
                        groups_prev_month[g.code]=0
                    if porcent_prev_year:
                        groups_dec_prev_year[g.code]=porcent_prev_year.porcent_per_month
                    else:
                        groups_dec_prev_year[g.code]=0
                    if porcent_acumulado:
                        groups_acum[g.code]=porcent_acumulado
                    else:
                        groups_acum[g.code]=0
                    if porcent_acumulado_prevyear:
                        groups_acum_month[g.code]=porcent_acumulado_prevyear
                    else:
                        groups_acum_month[g.code]=0

                    if g.formula_porcent:
                        calmesporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_real,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                        calmesprevporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_prev_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                        calbudgetmesporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_budget_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                        caldec_prev_yearporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_dec_prev_year,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                        calgroups_acumporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_acum,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                        calbudget_month_lyporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_budget_month_ly,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                        calacum_monthporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_acum_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                        if calmesporc:
                            groups_real_porc[g.code]=calmesporc
                        if calmesprevporc:
                            groups_prev_month_porc[g.code]=calmesprevporc
                        if calbudgetmesporc:
                            groups_budget_month_porc[g.code]=calbudgetmesporc
                        if caldec_prev_yearporc:
                            groups_dec_prev_year_porc[g.code]=caldec_prev_yearporc
                        if calgroups_acumporc:
                            groups_acum_porc[g.code]=calgroups_acumporc
                        if calbudget_month_lyporc:
                            groups_budget_month_ly_porc[g.code]=calbudget_month_lyporc
                        if calacum_monthporc:
                            groups_acum_month_porc[g.code]=calacum_monthporc

                    if g.acum_invisible:
                        pass
                    else:
                        lines.append({
                        'id': g.id,
                        'name':g.name,
                        'level': g.level,
                        'class': 'activo',
                        'columns':[
                        {'name':self.format_value(groups_real.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                        {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_real_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                        {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_prev_month_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                        {'name': '' if g.has_a_budget==False else self.format_value(groups_budget_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                        {'name': '' if g.has_a_budget==False or g.formula_porcent==False else "{:.2%}".format(groups_budget_month_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                        {'name': '' if g.formula_porcent==False else  "{:.2%}".format(groups_dec_prev_year_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(groups_acum.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                        {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_acum_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                        {'name': '' if g.has_a_budget==False else self.format_value(groups_budget_month_ly.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                        {'name': '' if g.has_a_budget==False or g.formula_porcent==False else "{:.2%}".format(groups_budget_month_ly_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(groups_acum_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                        {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_acum_month_porc.get(g.code,0)*signo),'class': 'number', 'style': 'white-space:nowrap;'}],
                        })
                elif g.volumen:

                    if g.volumen_ventas=='TONELADAS FACTURADAS CAJAS':
                        #BOX
                        volmonth = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',fields.Date.from_string(date_from),fields.Date.from_string(date_to),False)
                        volmonth_budget = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',fields.Date.from_string(date_from),fields.Date.from_string(date_to),True)
                        volmonthlast = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1),False)
                        vollastyear =  self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',fields.Date.from_string(date_from)+relativedelta(years=-1),fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1),False)
                        volmonthacum = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to),False)
                        volmonthacum_budget = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to),True)
                        volmonthacumly = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1),fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1),False)


                        lines.append({
                        'id': g.id,
                        'name':g.name,
                        'level':  g.level,
                        'class': 'toncaj',
                        'columns':[
                        {'name': "{:,}".format(round(volmonth)) if volmonth else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volmonthlast)) if volmonthlast else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volmonth_budget)) if volmonth_budget else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(vollastyear)) if vollastyear else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volmonthacum)) if volmonthacum else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volmonthacum_budget)) if volmonthacum_budget else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volmonthacumly)) if volmonthacumly else 0},
                        {'name': ''}
                        ],
                        })

                    elif g.volumen_ventas=='TONELADAS FACTURADAS PAPEL':
                        #PAPER
                        volpmonth = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',fields.Date.from_string(date_from),fields.Date.from_string(date_to),False)
                        volpmonth_budget = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',fields.Date.from_string(date_from),fields.Date.from_string(date_to),True)
                        volpmonthlast = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1),False)
                        volplastyear =  self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',fields.Date.from_string(date_from)+relativedelta(years=-1),fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1),False)
                        volpmonthacum = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to),False)
                        volpmonthacum_budget = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to),True)
                        volpmonthacumly = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1),fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1),False)


                        #LINES PAPER
                        lines.append({
                        'id': g.id,
                        'name':g.name,
                        'level':g.level,
                        'class': 'tonpap',
                        'columns':[
                        {'name': "{:,}".format(round(volpmonth)) if volpmonth else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volpmonthlast)) if volpmonthlast else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volpmonth_budget)) if volpmonth_budget else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volplastyear)) if volplastyear else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volpmonthacum)) if volpmonthacum else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volpmonthacum_budget)) if volpmonthacum_budget else 0},
                        {'name': ''},
                        {'name': "{:,}".format(round(volpmonthacumly)) if volpmonthacumly else 0},
                        {'name': ''}
                        ],
                        })


                # if g.formula==False:
                #     if g.title:
                #         if g.titulo_porcent==False:
                #             lines.append({
                #             'id': g.id,
                #             'name': g.name,
                #             'level': g.level,
                #             'class': 'activo',
                #             'columns':[
                #             {'name':''},
                #             {'name': ''},
                #             {'name':''},
                #             {'name': ''},
                #             {'name':''},
                #             {'name': ''},
                #             {'name':''},
                #             {'name': ''},
                #             {'name':''},
                #             {'name': ''},
                #             {'name':''},
                #             {'name': ''},
                #             {'name':''},
                #             {'name': ''}
                #             ],
                #             })
                #         elif g.titulo_porcent:
                #             lines.append({
                #             'id': g.id,
                #             'name': g.name,
                #             'level': g.level,
                #             'class': 'activo',
                #             'columns':[
                #             {'name':''},
                #             {'name': '%'},
                #             {'name':''},
                #             {'name': '%'},
                #             {'name':''},
                #             {'name': '%'},
                #             {'name':''},
                #             {'name': '%'},
                #             {'name':''},
                #             {'name': '%'},
                #             {'name':''},
                #             {'name': '%'},
                #             {'name':''},
                #             {'name': '%'}
                #             ],
                #             })
                #
                #     else:
                #
                #         if g.caculate_especial_cventa:
                #
                #             # balance_acumulado=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                #             # balance_acumulado_month=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=fields.Date.from_string(date_to)+relativedelta(years=-1))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                #             porcentaje=self.env['porcent.cost.sale'].search(['&','&',('name','=',g.costo_venta_id.id),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_to))])
                #             porcent_prev_month=self.env['porcent.cost.sale'].search(['&','&',('name','=',g.costo_venta_id.id),('date_from','>=',fields.Date.from_string(date_from)+relativedelta(months=-1)),('date_to','<=',fields.Date.from_string(date_from)+timedelta(days=-1))])
                #             porcent_prev_year=self.env['porcent.cost.sale'].search(['&','&',('name','=',g.costo_venta_id.id),('date_from','>=',fields.Date.from_string(date_from)+relativedelta(years=-1)),('date_to','<=',fields.Date.from_string(date_to)+relativedelta(years=-1))])
                #             porcent_acumulado=self._get_cost_sales(g.costo_venta_id.id,self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to))
                #             porcent_acumulado_prevyear=self._get_cost_sales(g.costo_venta_id.id,self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1),fields.Date.from_string(date_to)+relativedelta(years=-1))
                #             if g.budget_nova_id:
                #                 budget_month=self._get_budget_statement(g.budget_nova_id.id,fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                #                 budget_month_ly=self._get_budget_statement(g.budget_nova_id.id,self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to))
                #                 if budget_month:
                #                     groups_budget_month[g.code]=budget_month
                #
                #                 if budget_month_ly:
                #                     groups_budget_month_ly[g.code]=budget_month_ly
                #
                #
                #             if porcentaje:
                #                 groups_real[g.code]=porcentaje.porcent_per_month
                #             else:
                #                 groups_real[g.code]=0
                #             if porcent_prev_month:
                #                 groups_prev_month[g.code]=porcent_prev_month.porcent_per_month
                #             else:
                #                 groups_prev_month[g.code]=0
                #             if porcent_prev_year:
                #                 groups_dec_prev_year[g.code]=porcent_prev_year.porcent_per_month
                #             else:
                #                 groups_dec_prev_year[g.code]=0
                #             if porcent_acumulado:
                #                 groups_acum[g.code]=porcent_acumulado
                #             else:
                #                 groups_acum[g.code]=0
                #             if porcent_acumulado_prevyear:
                #                 groups_acum_month[g.code]=porcent_acumulado_prevyear
                #             else:
                #                 groups_acum_month[g.code]=0
                #             # if balance_acumulado:
                #             #     if porcentaje:
                #             #         groups_acum[g.code]=(balance_acumulado[0]*porcentaje.porcent)/100
                #             #     else:
                #             #         groups_acum[g.code]=balance_acumulado[0]
                #             #
                #             # if balance_acumulado_month:
                #             #     if porcentaje:
                #             #         groups_acum_month[g.code]=(balance_acumulado_month[0]*porcentaje.porcent)/100
                #             #     else:
                #             #         groups_acum_month[g.code]=balance_acumulado_month[0]
                #             if g.formula_porcent:
                #                 calmesporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_real,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #                 calmesprevporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_prev_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #                 calbudgetmesporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_budget_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #                 caldec_prev_yearporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_dec_prev_year,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #                 calgroups_acumporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_acum,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #                 calbudget_month_lyporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_budget_month_ly,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #                 calacum_monthporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_acum_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #                 if calmesporc:
                #                     groups_real_porc[g.code]=calmesporc
                #                 if calmesprevporc:
                #                     groups_prev_month_porc[g.code]=calmesprevporc
                #                 if calbudgetmesporc:
                #                     groups_budget_month_porc[g.code]=calbudgetmesporc
                #                 if caldec_prev_yearporc:
                #                     groups_dec_prev_year_porc[g.code]=caldec_prev_yearporc
                #                 if calgroups_acumporc:
                #                     groups_acum_porc[g.code]=calgroups_acumporc
                #                 if calbudget_month_lyporc:
                #                     groups_budget_month_ly_porc[g.code]=calbudget_month_lyporc
                #                 if calacum_monthporc:
                #                     groups_acum_month_porc[g.code]=calacum_monthporc
                #
                #
                #
                #
                #
                #
                #             lines.append({
                #             'id': g.id,
                #             'name':g.name,
                #             'level': g.level,
                #             'class': 'activo',
                #             'columns':[
                #             {'name':self.format_value(groups_real.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name':'' if g.formula_porcent==False else "{:.2%}".format(groups_real_porc.get(g.code,0)*signo)},
                #             {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_prev_month_porc.get(g.code,0)*signo)},
                #             {'name':'' if g.has_a_budget==False else self.format_value(groups_budget_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name':'' if g.has_a_budget==False or g.formula_porcent==False else "{:.2%}".format(groups_budget_month_porc.get(g.code,0)*signo)},
                #             {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': '' if g.formula_porcent==False else  "{:.2%}".format(groups_dec_prev_year_porc.get(g.code,0)*signo)},
                #             {'name':self.format_value(groups_acum.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_acum_porc.get(g.code,0)*signo)},
                #             {'name': '' if g.has_a_budget==False else self.format_value(groups_budget_month_ly.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': '' if g.has_a_budget==False or g.formula_porcent==False else "{:.2%}".format(groups_budget_month_ly_porc.get(g.code,0)*signo)},
                #             {'name':self.format_value(groups_acum_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_acum_month_porc.get(g.code,0)*signo)}],
                #             })
                #
                #         elif g.volumen:
                #             if g.volumen_ventas=='TONELADAS FACTURADAS CAJAS':
                #                 #BOX
                #                 volmonth = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',fields.Date.from_string(date_from),fields.Date.from_string(date_to),False)
                #                 volmonth_budget = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',fields.Date.from_string(date_from),fields.Date.from_string(date_to),True)
                #                 volmonthlast = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1),False)
                #                 vollastyear =  self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',fields.Date.from_string(date_from)+relativedelta(years=-1),fields.Date.from_string(date_to)+relativedelta(years=-1),False)
                #                 volmonthacum = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to),False)
                #                 volmonthacum_budget = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to),True)
                #                 volmonthacumly = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS CAJAS',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1),fields.Date.from_string(date_to)+relativedelta(years=-1),False)
                #
                #
                #                 lines.append({
                #                 'id': g.id,
                #                 'name':g.name,
                #                 'level':  g.level,
                #                 'class': 'toncaj',
                #                 'columns':[
                #                 {'name': "{:,}".format(round(volmonth)) if volmonth else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volmonthlast)) if volmonthlast else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volmonth_budget)) if volmonth_budget else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(vollastyear)) if vollastyear else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volmonthacum)) if volmonthacum else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volmonthacum_budget)) if volmonthacum_budget else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volmonthacumly)) if volmonthacumly else 0},
                #                 {'name': ''}
                #                 ],
                #                 })
                #
                #             elif g.volumen_ventas=='TONELADAS FACTURADAS PAPEL':
                #                 #PAPER
                #                 volpmonth = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',fields.Date.from_string(date_from),fields.Date.from_string(date_to),False)
                #                 volpmonth_budget = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',fields.Date.from_string(date_from),fields.Date.from_string(date_to),True)
                #                 volpmonthlast = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1),False)
                #                 volplastyear =  self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',fields.Date.from_string(date_from)+relativedelta(years=-1),fields.Date.from_string(date_to)+relativedelta(years=-1),False)
                #                 volpmonthacum = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to),False)
                #                 volpmonthacum_budget = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to),True)
                #                 volpmonthacumly = self._get_volumen_sale_boxpaper('TONELADAS FACTURADAS PAPEL',self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1),fields.Date.from_string(date_to)+relativedelta(years=-1),False)
                #
                #
                #                 #LINES PAPER
                #                 lines.append({
                #                 'id': g.id,
                #                 'name':g.name,
                #                 'level':g.level,
                #                 'class': 'tonpap',
                #                 'columns':[
                #                 {'name': "{:,}".format(round(volpmonth)) if volpmonth else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volpmonthlast)) if volpmonthlast else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volpmonth_budget)) if volpmonth_budget else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volplastyear)) if volplastyear else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volpmonthacum)) if volpmonthacum else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volpmonthacum_budget)) if volpmonthacum_budget else 0},
                #                 {'name': ''},
                #                 {'name': "{:,}".format(round(volpmonthacumly)) if volpmonthacumly else 0},
                #                 {'name': ''}
                #                 ],
                #                 })
                #         else:
                #             if g.group_finantial_id:
                #                 balance=self.with_context(date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to) )._balance_initial(options,line_id,str(g.group_finantial_id.id))
                #                 balance_prev_month=self.with_context(date_from=fields.Date.from_string(date_from)+relativedelta(months=-1), date_to=fields.Date.from_string(date_from)+timedelta(days=-1) )._balance_initial(options,line_id,str(g.group_finantial_id.id))
                #                 balance_prev_year=self.with_context(date_from=fields.Date.from_string(date_from)+relativedelta(years=-1), date_to=fields.Date.from_string(date_to)+relativedelta(years=-1) )._balance_initial(options,line_id,str(g.group_finantial_id.id))
                #                 balance_acumulado=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                #                 balance_acumulado_month=self.with_context(date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=fields.Date.from_string(date_to)+relativedelta(years=-1))._balance_initial(options,line_id,str(g.group_finantial_id.id))
                #                 if balance:
                #                     groups_real[g.code]=balance[0]
                #                 if balance_prev_month:
                #                     groups_prev_month[g.code]=balance_prev_month[0]
                #                 if balance_prev_year:
                #                     groups_dec_prev_year[g.code]=balance_prev_year[0]
                #                 if balance_acumulado:
                #                     groups_acum[g.code]=balance_acumulado[0]
                #                 if balance_acumulado_month:
                #                     groups_acum_month[g.code]=balance_acumulado_month[0]
                #
                #             if g.budget_nova_id:
                #                 budget_month=self._get_budget_statement(g.budget_nova_id.id,fields.Date.from_string(date_from),fields.Date.from_string(date_to))
                #                 budget_month_ly=self._get_budget_statement(g.budget_nova_id.id,self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'],fields.Date.from_string(date_to))
                #                 if budget_month:
                #                     groups_budget_month[g.code]=budget_month
                #                 if budget_month_ly:
                #                     groups_budget_month_ly[g.code]=budget_month_ly
                #
                #
                #
                #
                #
                #             lines.append({
                #             'id': g.id,
                #             'name':g.name,
                #             'level': g.level,
                #             'class': 'activo',
                #             'columns':[
                #             {'name':self.format_value(groups_real.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': ''},
                #             {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': ''},
                #             {'name':'' if g.has_a_budget==False else self.format_value(groups_budget_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': ''},
                #             {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': ''},
                #             {'name':self.format_value(groups_acum.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': ''},
                #             {'name': '' if g.has_a_budget==False else self.format_value(groups_budget_month_ly.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': ''},
                #             {'name':self.format_value(groups_acum_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #             {'name': ''}],
                #             })
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

                # else:
                #     mesreal=0
                #     mesanterior=0
                #     mespresupuesto=0
                #     anioanterior=0
                #     realacumulado=0
                #     presupuestoacumulado=0
                #     acumuladoañoanterior=0
                #     if g.expresion:
                #
                #         mesreal=self._calculate_formula(options,line_id,g.expresion,groups_real,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #         mesanterior=self._calculate_formula(options,line_id,g.expresion,groups_prev_month,date_from=fields.Date.from_string(date_from)+relativedelta(months=-1), date_to=fields.Date.from_string(date_from)+timedelta(days=-1))
                #         mespresupuesto=self._calculate_formula(options,line_id,g.expresion,groups_budget_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #         anioanterior=self._calculate_formula(options,line_id,g.expresion,groups_dec_prev_year,date_from=fields.Date.from_string(date_from)+relativedelta(years=-1), date_to=fields.Date.from_string(date_to)+relativedelta(years=-1))
                #         realacumulado=self._calculate_formula(options,line_id,g.expresion,groups_acum,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))
                #         presupuestoacumulado=self._calculate_formula(options,line_id,g.expresion,groups_budget_month_ly,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))
                #         acumuladoanioanterior=self._calculate_formula(options,line_id,g.expresion,groups_acum_month,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=fields.Date.from_string(date_to)+relativedelta(years=-1))
                #         if mesreal:
                #             groups_real[g.code]=mesreal
                #         if mesanterior:
                #             groups_prev_month[g.code]=mesanterior
                #         if mespresupuesto:
                #             groups_budget_month[g.code]=mespresupuesto
                #         if anioanterior:
                #             groups_dec_prev_year[g.code]=anioanterior
                #         if realacumulado:
                #             groups_acum[g.code]=realacumulado
                #         if presupuestoacumulado:
                #             groups_budget_month_ly[g.code]=presupuestoacumulado
                #         if acumuladoanioanterior:
                #             groups_acum_month[g.code]=acumuladoanioanterior
                #
                #         if g.title:
                #             if g.titulo_porcent==False:
                #                 lines.append({
                #                 'id': g.id,
                #                 'name': g.name,
                #                 'level': g.level,
                #                 'class': 'activo',
                #                 'columns':[
                #                 {'name':''},
                #                 {'name': ''},
                #                 {'name':''},
                #                 {'name': ''},
                #                 {'name':''},
                #                 {'name': ''},
                #                 {'name':''},
                #                 {'name': ''},
                #                 {'name':''},
                #                 {'name': ''},
                #                 {'name':''},
                #                 {'name': ''},
                #                 {'name':''},
                #                 {'name': ''}
                #                 ],
                #                 })
                #             elif g.titulo_porcent:
                #                 lines.append({
                #                 'id': g.id,
                #                 'name': g.name,
                #                 'level': g.level,
                #                 'class': 'activo',
                #                 'columns':[
                #                 {'name':''},
                #                 {'name': '%'},
                #                 {'name':''},
                #                 {'name': '%'},
                #                 {'name':''},
                #                 {'name': '%'},
                #                 {'name':''},
                #                 {'name': '%'},
                #                 {'name':''},
                #                 {'name': '%'},
                #                 {'name':''},
                #                 {'name': '%'},
                #                 {'name':''},
                #                 {'name': '%'}
                #                 ],
                #                 })
                #         elif g.acum_invisible and g.title==False:
                #             pass
                #         else:
                #             if g.formula_porcent==False:
                #                 lines.append({
                #                 'id': g.id,
                #                 'name':g.name,
                #                 'level': g.level,
                #                 'class': 'activo',
                #                 'columns':[
                #                 {'name':self.format_value(groups_real.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': ''},
                #                 {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': ''},
                #                 {'name':'' if g.has_a_budget==False else self.format_value(groups_budget_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': ''},
                #                 {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': ''},
                #                 {'name':self.format_value(groups_acum.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': ''},
                #                 {'name': '' if g.has_a_budget==False else self.format_value(groups_budget_month_ly.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': ''},
                #                 {'name':self.format_value(groups_acum_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': ''}],
                #                 })
                #
                #             else:
                #
                #                 calmesporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_real,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #                 calmesprevporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_prev_month,date_from=fields.Date.from_string(date_from)+relativedelta(months=-1), date_to=fields.Date.from_string(date_from)+timedelta(days=-1))
                #                 calbudgetmesporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_budget_month,date_from=fields.Date.from_string(date_from), date_to=fields.Date.from_string(date_to))
                #                 caldec_prev_yearporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_dec_prev_year,date_from=fields.Date.from_string(date_from)+relativedelta(years=-1), date_to = fields.Date.from_string(date_to)+relativedelta(years=-1))
                #                 calgroups_acumporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_acum,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))
                #                 calbudget_month_lyporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_budget_month_ly,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'], date_to=fields.Date.from_string(date_to))
                #                 calacum_monthporc=self._calculate_formula(options,line_id,g.expresion_porcent,groups_acum_month,date_from=self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from']+relativedelta(years=-1), date_to=fields.Date.from_string(date_to)+relativedelta(years=-1))
                #                 if calmesporc:
                #                     groups_real_porc[g.code]=calmesporc
                #                 if calmesprevporc:
                #                     groups_prev_month_porc[g.code]=calmesprevporc
                #                 if calbudgetmesporc:
                #                     groups_budget_month_porc[g.code]=calbudgetmesporc
                #                 if caldec_prev_yearporc:
                #                     groups_dec_prev_year_porc[g.code]=caldec_prev_yearporc
                #                 if calgroups_acumporc:
                #                     groups_acum_porc[g.code]=calgroups_acumporc
                #                 if calbudget_month_lyporc:
                #                     groups_budget_month_ly_porc[g.code]=calbudget_month_lyporc
                #                 if calacum_monthporc:
                #                     groups_acum_month_porc[g.code]=calacum_monthporc
                #
                #                 lines.append({
                #                 'id': g.id,
                #                 'name':g.name,
                #                 'level': g.level,
                #                 'class': 'activo',
                #                 'columns':[
                #                 {'name':self.format_value(groups_real.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name':'' if g.formula_porcent==False else "{:.2%}".format(groups_real_porc.get(g.code,0)*signo)},
                #                 {'name':self.format_value(groups_prev_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_prev_month_porc.get(g.code,0)*signo)},
                #                 {'name':'' if g.has_a_budget==False else self.format_value(groups_budget_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name':'' if g.has_a_budget==False or g.formula_porcent==False else "{:.2%}".format(groups_budget_month_porc.get(g.code,0)*signo)},
                #                 {'name':self.format_value(groups_dec_prev_year.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': '' if g.formula_porcent==False else  "{:.2%}".format(groups_dec_prev_year_porc.get(g.code,0)*signo)},
                #                 {'name':self.format_value(groups_acum.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_acum_porc.get(g.code,0)*signo)},
                #                 {'name': '' if g.has_a_budget==False else self.format_value(groups_budget_month_ly.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': '' if g.has_a_budget==False or g.formula_porcent==False else "{:.2%}".format(groups_budget_month_ly_porc.get(g.code,0)*signo)},
                #                 {'name':self.format_value(groups_acum_month.get(g.code,0)*signo),'class': 'number color-red' if g.color_red else 'number'},
                #                 {'name': '' if g.formula_porcent==False else "{:.2%}".format(groups_acum_month_porc.get(g.code,0)*signo)}],
                #                 })




        return lines


    @api.model
    def _get_report_name(self):
        return _('Estado de Resultados')
