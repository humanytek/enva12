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


class ReportsReceiptsNova(models.AbstractModel):
    _name = "reports.receipts.nova"
    _description = "Reports Receipts"
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}

    def _get_columns_name(self, options):
        return [
        {'name': _('CLIENTE'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('META'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('FACTURACION'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('ACUMULADO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('DIF'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('CUMPLIMIENTO'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('PPTO DIA'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('%'), 'class': 'number', 'style': 'text-align: center;white-space:nowrap;'},
        {'name': _('TENDENCIA'), 'class': 'number', 'style': 'text-align: left;white-space:nowrap;'},
        {'name': _('MES ANTERIOR'), 'class': 'number', 'style': 'text-align: left;white-space:nowrap;'},
        {'name': _('AÑO ANTERIOR'), 'class': 'number', 'style': 'text-align: left;white-space:nowrap;'},
        {'name': _('COMENTARIOS'), 'class': 'number', 'style': 'text-align: left;white-space:nowrap;'},
        ]



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

    def _partner_line(self,options,line_id,partner):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            (SELECT
                    rp.name as partner,
                    rp.id as partner_id
                    FROM account_payment ap
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=ap.partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE ap.payment_date >= '"""+date_from+"""' AND ap.payment_date <= '"""+date_to+"""'
                    AND ap.state in ('posted','reconciled') AND ap.payment_type in ('inbound') AND rp.id is not NULL
                    AND rpc.name='CORRUGADO'
                    AND rp.name not in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.')
                    GROUP BY rp.id,rp.name
                    )
                    UNION(
            SELECT
                    rp.name as partner,rp.id as partner_id
                    FROM budget_goal_receipts bgr
                    LEFT JOIN res_partner rp ON rp.id=bgr.name
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=bgr.name
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE bgr.date_from >= '"""+date_from+"""' AND bgr.date_to <= '"""+str(df)+"""'
                    AND rpc.name='CORRUGADO'
                    AND rp.name not in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.')
                    GROUP BY rp.id,rp.name
                    )
            ORDER BY partner




        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _partner_line_a(self,options,line_id,partner):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            (SELECT
                    rp.name as partner,
                    rp.id as partner_id
                    FROM account_payment ap
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=ap.partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE ap.payment_date >= '"""+date_from+"""' AND ap.payment_date <= '"""+date_to+"""'
                    AND ap.state in ('posted','reconciled') AND ap.payment_type in ('inbound') AND rp.id is not NULL
                    AND rpc.name='CORRUGADO'
                    AND rp.name in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.')
                    GROUP BY rp.id,rp.name
                    )
                    UNION(
            SELECT
                    rp.name as partner,rp.id as partner_id
                    FROM budget_goal_receipts bgr
                    LEFT JOIN res_partner rp ON rp.id=bgr.name
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=bgr.name
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE bgr.date_from >= '"""+date_from+"""' AND bgr.date_to <= '"""+str(df)+"""'
                    AND rpc.name='CORRUGADO'
                    AND rp.name in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.')
                    GROUP BY rp.id,rp.name
                    )
            ORDER BY partner




        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _payment_line(self,options,line_id,partner,datefrom,dateto):

        sql_query ="""

            SELECT

                    SUM(ap.amount*ap.tipocambio) as monto
                    FROM account_payment ap
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id

                    WHERE ap.payment_date >= '"""+datefrom+"""' AND ap.payment_date <= '"""+dateto+"""'
                    AND rp.name = '"""+partner+"""' AND ap.state in ('posted','reconciled') AND ap.payment_type in ('inbound')


        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _account_invoice(self,options,line_id,partner):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            SELECT

                    SUM(ai.amount_total_company_signed) as residual
                    FROM account_invoice ai
                    LEFT JOIN res_partner rp ON rp.id=ai.commercial_partner_id

                    WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                    AND ai.commercial_partner_id="""+partner+""" AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'



        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _get_budget_goal(self, nstate, date_f,date_t):
        budget=self.env['budget.goal.receipts'].search(['&','&',('name','=',nstate),('date_from','>=',date_f),('date_to','<=',date_t)])

        budgetacum=0
        if budget:
            for b in budget:
                budgetacum+=b.goal

        return budgetacum

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        partner = self._partner_line(options,line_id,False)
        partnera = self._partner_line_a(options,line_id,False)
        df=fields.Date.from_string(date_from)

        if partner:

            tbudget=0
            tfacturacion=0
            tacumulado=0
            tacumuladom=0
            tacumuladoy=0
            tcumplimiento=0
            tpptodia=0
            tporcentaje=0
            ttendencia=0
            for p in partner:
                facturacion=0
                acumulado=0
                acumuladom=0
                acumuladoy=0
                cumplimiento=0
                pptodia=0
                porcentaje=0
                tendencia=0
                budget=self._get_budget_goal(p['partner_id'], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                m=self._payment_line(options,line_id,str(p['partner']),str(fields.Date.from_string(date_from)),str(fields.Date.from_string(date_to)))
                m_ant=self._payment_line(options,line_id,str(p['partner']),str(fields.Date.from_string(date_from)+relativedelta(months=-1)),str(fields.Date.from_string(date_from)+timedelta(days=-1)))
                m_anio_ant=self._payment_line(options,line_id,str(p['partner']),str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))

                r=self._account_invoice(options,line_id,str(p['partner_id']))
                bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
                comentarios = self.env['budget.goal.receipts'].search(['&','&',('name','=',p['partner_id']),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))])
                if r[0]['residual'] != None:
                    facturacion=r[0]['residual']
                    tfacturacion+=r[0]['residual']
                else:
                    facturacion=0
                    tfacturacion+=0

                if m[0]['monto'] != None:
                    acumulado=m[0]['monto']
                    tacumulado+=m[0]['monto']
                else:
                    acumulado=0
                    tacumulado+=0

                if m_ant[0]['monto'] != None:
                    acumuladom=m_ant[0]['monto']
                    tacumuladom+=m_ant[0]['monto']
                else:
                    acumuladom=0
                    tacumuladom+=0

                if m_anio_ant[0]['monto'] != None:
                    acumuladoy=m_anio_ant[0]['monto']
                    tacumuladoy+=m_anio_ant[0]['monto']
                else:
                    acumuladoy=0
                    tacumuladoy+=0

                if budget!=0:
                    if m[0]['monto']!=None:
                        if m[0]['monto']!=0:
                            cumplimiento=m[0]['monto']/budget

                        else:
                            cumplimiento=0

                    else:
                        cumplimiento=0

                else:
                    cumplimiento=0


                if bussines_days.bussines_days!=False or bussines_days.bussines_days!=0:
                    if budget!=0:
                        if self._billed_days(options,line_id)!=False:
                            pptodia=(budget/bussines_days.bussines_days)*self._billed_days(options,line_id)
                            tpptodia+=(budget/bussines_days.bussines_days)*self._billed_days(options,line_id)
                        else:
                            pptodia=(budget/bussines_days.bussines_days)*0
                            tpptodia+=(budget/bussines_days.bussines_days)*0

                if pptodia!=0:
                    if acumulado!=0:
                        porcentaje=acumulado/pptodia

                    else:
                        porcentaje=0

                else:
                    porcentaje=0


                if self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0:
                    if acumulado!=0:
                        if bussines_days.bussines_days!=False:
                            tendencia=(acumulado/self._billed_days(options,line_id))*bussines_days.bussines_days
                            ttendencia+=(acumulado/self._billed_days(options,line_id))*bussines_days.bussines_days
                        else:
                            tendencia=(acumulado/self._billed_days(options,line_id))*0
                            ttendencia+=(acumulado/self._billed_days(options,line_id))*0


                lines.append({
                'id': str(p['partner_id']),
                'name': str(p['partner']) ,
                'level': 2,
                'class': 'payment',
                'columns':[
                        {'name':self.format_value(budget) if budget else self.format_value(0) , 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(facturacion) , 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(acumulado) , 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(budget-acumulado) , 'style': 'white-space:nowrap;'},
                        {'name':"{:.0%}".format(cumplimiento), 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(pptodia) , 'style': 'white-space:nowrap;'},
                        {'name':"{:.0%}".format(porcentaje) , 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(tendencia), 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(acumuladom) , 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(acumuladoy), 'style': 'white-space:nowrap;'},
                        {'name':comentarios.note if comentarios.note!=False else '' , 'style': 'text-align: left; white-space:nowrap;'},


                ],

                })
                if budget:
                    tbudget+=budget
                else:
                    tbudget+=0

                if tbudget!=0:
                    if tacumulado!=None:
                        if tacumulado!=0:
                            tcumplimiento+=tacumulado/tbudget
                        else:
                            tcumplimiento+=0
                    else:
                        tcumplimiento+=0
                else:
                    tcumplimiento+=0

                if tpptodia!=0:
                    if tacumulado!=0:
                        tporcentaje+=tacumulado/tpptodia
                    else:
                        tporcentaje+=0
                else:
                    tporcentaje+=0



            lines.append({
            'id': 'TOTAL',
            'name': 'TOTAL' ,
            'level': 1,
            'class': 'payment',
            'columns':[
                    {'name':self.format_value(tbudget), 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tfacturacion) , 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tacumulado) , 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tbudget-tacumulado) , 'style': 'white-space:nowrap;'},
                    {'name':"{:.0%}".format(tcumplimiento), 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tpptodia) , 'style': 'white-space:nowrap;'},
                    {'name':"{:.0%}".format(tporcentaje) , 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(ttendencia), 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tacumuladom) , 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tacumuladoy), 'style': 'white-space:nowrap;'},
                    {'name':''},


            ],

            })

        if partnera:
            lines.append({
            'id': 'cliente',
            'name': '' ,
            'level': 0,
            'class': 'payment',
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


            ],

            })

            tbudget=0
            tfacturacion=0
            tacumulado=0
            tacumuladom=0
            tacumuladoy=0
            tcumplimiento=0
            tpptodia=0
            tporcentaje=0
            ttendencia=0
            for p in partnera:
                facturacion=0
                acumulado=0
                acumuladom=0
                acumuladoy=0
                cumplimiento=0
                pptodia=0
                porcentaje=0
                tendencia=0
                budget=self._get_budget_goal(p['partner_id'], fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                m=self._payment_line(options,line_id,str(p['partner']),str(fields.Date.from_string(date_from)),str(fields.Date.from_string(date_to)))
                m_ant=self._payment_line(options,line_id,str(p['partner']),str(fields.Date.from_string(date_from)+relativedelta(months=-1)),str(fields.Date.from_string(date_from)+timedelta(days=-1)))
                m_anio_ant=self._payment_line(options,line_id,str(p['partner']),str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))

                r=self._account_invoice(options,line_id,str(p['partner_id']))
                bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
                comentarios = self.env['budget.goal.receipts'].search(['&','&',('name','=',p['partner_id']),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))])
                if r[0]['residual'] != None:
                    facturacion=r[0]['residual']
                    tfacturacion+=r[0]['residual']
                else:
                    facturacion=0
                    tfacturacion+=0

                if m[0]['monto'] != None:
                    acumulado=m[0]['monto']
                    tacumulado+=m[0]['monto']
                else:
                    acumulado=0
                    tacumulado+=0

                if m_ant[0]['monto'] != None:
                    acumuladom=m_ant[0]['monto']
                    tacumuladom+=m_ant[0]['monto']
                else:
                    acumuladom=0
                    tacumuladom+=0

                if m_anio_ant[0]['monto'] != None:
                    acumuladoy=m_anio_ant[0]['monto']
                    tacumuladoy+=m_anio_ant[0]['monto']
                else:
                    acumuladoy=0
                    tacumuladoy+=0

                if budget!=0:
                    if m[0]['monto']!=None:
                        if m[0]['monto']!=0:
                            cumplimiento=m[0]['monto']/budget

                        else:
                            cumplimiento=0

                    else:
                        cumplimiento=0

                else:
                    cumplimiento=0


                if bussines_days.bussines_days!=False or bussines_days.bussines_days!=0:
                    if budget!=0:
                        if self._billed_days(options,line_id)!=False:
                            pptodia=(budget/bussines_days.bussines_days)*self._billed_days(options,line_id)
                            tpptodia+=(budget/bussines_days.bussines_days)*self._billed_days(options,line_id)
                        else:
                            pptodia=(budget/bussines_days.bussines_days)*0
                            tpptodia+=(budget/bussines_days.bussines_days)*0

                if pptodia!=0:
                    if acumulado!=0:
                        porcentaje=acumulado/pptodia

                    else:
                        porcentaje=0

                else:
                    porcentaje=0


                if self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0:
                    if acumulado!=0:
                        if bussines_days.bussines_days!=False:
                            tendencia=(acumulado/self._billed_days(options,line_id))*bussines_days.bussines_days
                            ttendencia+=(acumulado/self._billed_days(options,line_id))*bussines_days.bussines_days
                        else:
                            tendencia=(acumulado/self._billed_days(options,line_id))*0
                            ttendencia+=(acumulado/self._billed_days(options,line_id))*0


                lines.append({
                'id': str(p['partner_id']),
                'name': str(p['partner']) ,
                'level': 2,
                'class': 'payment',
                'columns':[
                        {'name':self.format_value(budget) if budget else self.format_value(0) , 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(facturacion) , 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(acumulado) , 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(budget-acumulado) , 'style': 'white-space:nowrap;'},
                        {'name':"{:.0%}".format(cumplimiento), 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(pptodia) , 'style': 'white-space:nowrap;'},
                        {'name':"{:.0%}".format(porcentaje) , 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(tendencia), 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(acumuladom) , 'style': 'white-space:nowrap;'},
                        {'name':self.format_value(acumuladoy), 'style': 'white-space:nowrap;'},
                        {'name':comentarios.note if comentarios.note!=False else '' , 'style': 'text-align: left; white-space:nowrap;'},


                ],

                })
                if budget:
                    tbudget+=budget
                else:
                    tbudget+=0

                if tbudget!=0:
                    if tacumulado!=None:
                        if tacumulado!=0:
                            tcumplimiento+=tacumulado/tbudget
                        else:
                            tcumplimiento+=0
                    else:
                        tcumplimiento+=0
                else:
                    tcumplimiento+=0

                if tpptodia!=0:
                    if tacumulado!=0:
                        tporcentaje+=tacumulado/tpptodia
                    else:
                        tporcentaje+=0
                else:
                    tporcentaje+=0



            lines.append({
            'id': 'TOTAL',
            'name': 'TOTAL' ,
            'level': 1,
            'class': 'payment',
            'columns':[
                    {'name':self.format_value(tbudget), 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tfacturacion) , 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tacumulado) , 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tbudget-tacumulado) , 'style': 'white-space:nowrap;'},
                    {'name':"{:.0%}".format(tcumplimiento), 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tpptodia) , 'style': 'white-space:nowrap;'},
                    {'name':"{:.0%}".format(tporcentaje) , 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(ttendencia), 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tacumuladom) , 'style': 'white-space:nowrap;'},
                    {'name':self.format_value(tacumuladoy), 'style': 'white-space:nowrap;'},
                    {'name':''},


            ],

            })

        return lines

    @api.model
    def _get_report_name(self):
        return _('Reportes de Ingresos Corrugado')
