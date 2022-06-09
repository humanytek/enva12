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
    _name = "reports.receipts.nova.acum"
    _description = "Reports Receipts"
    _inherit = 'account.report'

    filter_date = {'mode': 'range', 'filter': 'this_month'}

    def _get_columns_name(self, options):
        return [
        {'name': _(''), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('META COBR MES'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('FACT DEL MES'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('COBR ACUM MES'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('META COBR VS META ACUM'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('CUMPL COBR MES'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('PPTO COBR DIA'), 'class': 'number', 'style': 'text-align: left; white-space:nowrap;'},
        {'name': _('% PPTO COBR DIA'), 'class': 'number', 'style': 'text-align: center;white-space:nowrap;'},
        {'name': _('TEND COBR MES'), 'class': 'number', 'style': 'text-align: left;white-space:nowrap;'},
        {'name': _('COBR MES ANTERIOR'), 'class': 'number', 'style': 'text-align: left;white-space:nowrap;'},
        {'name': _('COBR MISMO MES AÑO ANTERIOR'), 'class': 'number', 'style': 'text-align: left;white-space:nowrap;'},
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

    def _get_tbudget_goal(self, date_f,date_t):
        budget=self.env['budget.goal.receipts'].search(['&',('date_from','>=',date_f),('date_to','<=',date_t)])

        budgetacum=0
        if budget:
            for b in budget:
                budgetacum+=b.goal

        return budgetacum

    def _get_tcbudget_goal(self,options,line_id):
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            SELECT

                    SUM(bgr.goal) as meta
                    FROM budget_goal_receipts bgr
                    LEFT JOIN res_partner rp ON rp.id=bgr.name
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=bgr.name
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE bgr.date_from >= '"""+date_from+"""' AND bgr.date_to <= '"""+str(df)+"""'
                    AND rpc.name in ('CORRUGADO') AND rp.name not in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.')



        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _get_tacbudget_goal(self,options,line_id):
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            SELECT

                    SUM(bgr.goal) as meta
                    FROM budget_goal_receipts bgr
                    LEFT JOIN res_partner rp ON rp.id=bgr.name
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=bgr.name
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE bgr.date_from >= '"""+date_from+"""' AND bgr.date_to <= '"""+str(df)+"""'
                    AND rpc.name in ('CORRUGADO') AND rp.name in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.')



        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _get_tpbudget_goal(self,options,line_id):
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            SELECT

                    SUM(bgr.goal) as meta
                    FROM budget_goal_receipts bgr
                    LEFT JOIN res_partner rp ON rp.id=bgr.name
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=bgr.name
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE bgr.date_from >= '"""+date_from+"""' AND bgr.date_to <= '"""+str(df)+"""'
                    AND rpc.name in ('PAPEL')



        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _taccount_invoice(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            SELECT

                    SUM(am.amount_total_signed) as residual
                    FROM account_move am
                    LEFT JOIN res_partner rp ON rp.id=am.commercial_partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=am.commercial_partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                    AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                    AND rpc.name in ('CORRUGADO','PAPEL')



        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _tcaccount_invoice(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            SELECT

                    SUM(am.amount_total_signed) as residual
                    FROM account_move am
                    LEFT JOIN res_partner rp ON rp.id=am.commercial_partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=am.commercial_partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                    AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                    AND rpc.name in ('CORRUGADO') AND rp.name not in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.')



        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _tacaccount_invoice(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            SELECT

                    SUM(am.amount_total_signed) as residual
                    FROM account_move am
                    LEFT JOIN res_partner rp ON rp.id=am.commercial_partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=am.commercial_partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                    AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                    AND rpc.name in ('CORRUGADO') AND rp.name in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.')



        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _tpaccount_invoice(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        sql_query ="""

            SELECT

                    SUM(am.amount_total_signed) as residual
                    FROM account_move am
                    LEFT JOIN res_partner rp ON rp.id=am.commercial_partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=am.commercial_partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                    AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                    AND rpc.name in ('PAPEL')



        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _tpayment_line(self,options,line_id,datefrom,dateto):

        sql_query ="""

            SELECT

                    SUM(ap.amount*ap.tipocambio) as monto
                    FROM account_payment ap
                    LEFT JOIN account_move am ON am.id = ap.move_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=ap.partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.date >= '"""+datefrom+"""' AND am.date <= '"""+dateto+"""'
                    AND am.state in ('posted','reconciled') AND ap.payment_type in ('inbound')
                    AND rpc.name in ('CORRUGADO','PAPEL')


        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _tcpayment_line(self,options,line_id,datefrom,dateto):

        sql_query ="""

            SELECT

                    SUM(ap.amount*ap.tipocambio) as monto
                    FROM account_payment ap
                    LEFT JOIN account_move am ON am.id = ap.move_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=ap.partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.date >= '"""+datefrom+"""' AND am.date <= '"""+dateto+"""'
                    AND am.state in ('posted','reconciled') AND ap.payment_type in ('inbound')
                    AND rpc.name in ('CORRUGADO') AND rp.name not in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.')


        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _tacpayment_line(self,options,line_id,datefrom,dateto):

        sql_query ="""

            SELECT

                    SUM(ap.amount*ap.tipocambio) as monto
                    FROM account_payment ap
                    LEFT JOIN account_move am ON am.id = ap.move_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=ap.partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.date >= '"""+datefrom+"""' AND am.date <= '"""+dateto+"""'
                    AND am.state in ('posted','reconciled') AND ap.payment_type in ('inbound')
                    AND rpc.name in ('CORRUGADO') AND rp.name in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.')


        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _tppayment_line(self,options,line_id,datefrom,dateto):

        sql_query ="""

            SELECT

                    SUM(ap.amount*ap.tipocambio) as monto
                    FROM account_payment ap
                    LEFT JOIN account_move am ON am.id = ap.move_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=ap.partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.date >= '"""+datefrom+"""' AND am.date <= '"""+dateto+"""'
                    AND am.state in ('posted','reconciled') AND ap.payment_type in ('inbound')
                    AND rpc.name in ('PAPEL')


        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)
        tfacturacion=0
        tcumplimiento=0
        tpptodia=0
        tporcentaje=0
        ttendencia=0
        tacumuladom=0
        tacumuladoy=0
        bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
        tbudget=self._get_tbudget_goal(fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
        tr=self._taccount_invoice(options,line_id)
        tm=self._tpayment_line(options,line_id,str(fields.Date.from_string(date_from)),str(fields.Date.from_string(date_to)))
        tm_ant=self._tpayment_line(options,line_id,str(fields.Date.from_string(date_from)+relativedelta(months=-1)),str(fields.Date.from_string(date_from)+timedelta(days=-1)))
        tm_anio_ant=self._tpayment_line(options,line_id,str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))

        if tr[0]['residual'] != None:
            tfacturacion=tr[0]['residual']
        else:
            tfacturacion=0

        if tm[0]['monto'] != None:
            tacumulado=tm[0]['monto']

        else:
            tacumulado=0

        if tm_ant[0]['monto'] != None:
            tacumuladom=tm_ant[0]['monto']

        else:
            tacumuladom=0

        if tm_anio_ant[0]['monto'] != None:
            tacumuladoy=tm_anio_ant[0]['monto']
        else:
            tacumuladoy=0


        if tbudget!=0:
            if tm[0]['monto']!=None:
                if tm[0]['monto']!=0:
                    tcumplimiento=tm[0]['monto']/tbudget

                else:
                    tcumplimiento=0

            else:
                tcumplimiento=0

        else:
            tcumplimiento=0

        if bussines_days.bussines_days_c!=False or bussines_days.bussines_days_c!=0:
            if tbudget!=0:
                if self._billed_days(options,line_id)!=False:
                    tpptodia=(tbudget/bussines_days.bussines_days_c)*self._billed_days(options,line_id)

                else:
                    tpptodia=(tbudget/bussines_days.bussines_days_c)*0

        if tpptodia!=0:
            if tacumulado!=0:
                tporcentaje=tacumulado/tpptodia

            else:
                tporcentaje=0

        else:
            tporcentaje=0


        if self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0:
            if tacumulado!=0:
                if bussines_days.bussines_days_c!=False:
                    ttendencia=(tacumulado/self._billed_days(options,line_id))*bussines_days.bussines_days_c

                else:
                    ttendencia=(tacumulado/self._billed_days(options,line_id))*0


        lines.append({
        'id': 'acum',
        'name': _('') ,
        'level': 1,
        'class': 'payment',
        'columns':[
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,

        ],
        })

        lines.append({
        'id': 'acum',
        'name': _('ACUMULADO CONCENTRADO') ,
        'level': 2,
        'class': 'payment',
        'columns':[
                {'name':self.format_value(tbudget) if tbudget else self.format_value(0), 'style': 'white-space:nowrap;'} ,
                {'name':self.format_value(tfacturacion) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tacumulado) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tbudget-tacumulado) , 'style': 'white-space:nowrap;'},
                {'name':"{:.0%}".format(tcumplimiento), 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tpptodia) , 'style': 'white-space:nowrap;'},
                {'name':"{:.0%}".format(tporcentaje) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(ttendencia), 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tacumuladom) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tacumuladoy), 'style': 'white-space:nowrap;'},

        ],
        })
        tcmeta=0
        tcfacturacion=0
        tccumplimiento=0
        tcpptodia=0
        tcporcentaje=0
        tctendencia=0
        tcacumuladom=0
        tcacumuladoy=0
        bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
        tcbudget=self._get_tcbudget_goal(options,line_id)
        tcr=self._tcaccount_invoice(options,line_id)
        tcm=self._tcpayment_line(options,line_id,str(fields.Date.from_string(date_from)),str(fields.Date.from_string(date_to)))
        tcm_ant=self._tcpayment_line(options,line_id,str(fields.Date.from_string(date_from)+relativedelta(months=-1)),str(fields.Date.from_string(date_from)+timedelta(days=-1)))
        tcm_anio_ant=self._tcpayment_line(options,line_id,str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))

        if tcbudget[0]['meta'] != None:
            tcmeta=tcbudget[0]['meta']
        else:
            tcmeta=0

        if tcr[0]['residual'] != None:
            tcfacturacion=tcr[0]['residual']
        else:
            tcfacturacion=0

        if tcm[0]['monto'] != None:
            tcacumulado=tcm[0]['monto']

        else:
            tcacumulado=0

        if tcm_ant[0]['monto'] != None:
            tcacumuladom=tcm_ant[0]['monto']

        else:
            tcacumuladom=0

        if tcm_anio_ant[0]['monto'] != None:
            tcacumuladoy=tcm_anio_ant[0]['monto']
        else:
            tcacumuladoy=0


        if tcmeta!=0:
            if tcm[0]['monto']!=None:
                if tcm[0]['monto']!=0:
                    tccumplimiento=tcm[0]['monto']/tcmeta

                else:
                    tccumplimiento=0

            else:
                tccumplimiento=0

        else:
            tcumplimiento=0

        if bussines_days.bussines_days_c!=False or bussines_days.bussines_days_c!=0:
            if tcmeta!=0:
                if self._billed_days(options,line_id)!=False:
                    tcpptodia=(tcmeta/bussines_days.bussines_days_c)*self._billed_days(options,line_id)

                else:
                    tcpptodia=(tcmeta/bussines_days.bussines_days_c)*0

        if tcpptodia!=0:
            if tcacumulado!=0:
                tcporcentaje=tcacumulado/tcpptodia

            else:
                tcporcentaje=0

        else:
            tcporcentaje=0


        if self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0:
            if tcacumulado!=0:
                if bussines_days.bussines_days_c!=False:
                    tctendencia=(tcacumulado/self._billed_days(options,line_id))*bussines_days.bussines_days_c

                else:
                    tctendencia=(tcacumulado/self._billed_days(options,line_id))*0


        lines.append({
        'id': 'acum',
        'name': _('') ,
        'level': 1,
        'class': 'payment',
        'columns':[
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,

        ],
        })

        lines.append({
        'id': 'acum',
        'name': _('CORRUGADO') ,
        'level': 2,
        'class': 'payment',
        'columns':[
                {'name':self.format_value(tcmeta), 'style': 'white-space:nowrap;'} ,
                {'name':self.format_value(tcfacturacion) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tcacumulado) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tcmeta-tcacumulado) , 'style': 'white-space:nowrap;'},
                {'name':"{:.0%}".format(tccumplimiento), 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tcpptodia) , 'style': 'white-space:nowrap;'},
                {'name':"{:.0%}".format(tcporcentaje) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tctendencia), 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tcacumuladom) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tcacumuladoy), 'style': 'white-space:nowrap;'},

        ],
        })

        tpmeta=0
        tpfacturacion=0
        tpcumplimiento=0
        tppptodia=0
        tpporcentaje=0
        tptendencia=0
        tpacumuladom=0
        tpacumuladoy=0
        bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
        tpbudget=self._get_tpbudget_goal(options,line_id)
        tpr=self._tpaccount_invoice(options,line_id)
        tpm=self._tppayment_line(options,line_id,str(fields.Date.from_string(date_from)),str(fields.Date.from_string(date_to)))
        tpm_ant=self._tppayment_line(options,line_id,str(fields.Date.from_string(date_from)+relativedelta(months=-1)),str(fields.Date.from_string(date_from)+timedelta(days=-1)))
        tpm_anio_ant=self._tppayment_line(options,line_id,str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))

        if tpbudget[0]['meta'] != None:
            tpmeta=tpbudget[0]['meta']
        else:
            tpmeta=0

        if tpr[0]['residual'] != None:
            tpfacturacion=tpr[0]['residual']
        else:
            tpfacturacion=0

        if tpm[0]['monto'] != None:
            tpacumulado=tpm[0]['monto']

        else:
            tpacumulado=0

        if tpm_ant[0]['monto'] != None:
            tpacumuladom=tpm_ant[0]['monto']

        else:
            tpacumuladom=0

        if tpm_anio_ant[0]['monto'] != None:
            tpacumuladoy=tpm_anio_ant[0]['monto']
        else:
            tpacumuladoy=0


        if tpmeta!=0:
            if tpm[0]['monto']!=None:
                if tpm[0]['monto']!=0:
                    tpcumplimiento=tpm[0]['monto']/tpmeta

                else:
                    tpcumplimiento=0

            else:
                tpcumplimiento=0

        else:
            tpumplimiento=0

        if bussines_days.bussines_days_c!=False or bussines_days.bussines_days_c!=0:
            if tpmeta!=0:
                if self._billed_days(options,line_id)!=False:
                    tppptodia=(tpmeta/bussines_days.bussines_days_c)*self._billed_days(options,line_id)

                else:
                    tppptodia=(tpmeta/bussines_days.bussines_days_c)*0

        if tppptodia!=0:
            if tpacumulado!=0:
                tpporcentaje=tpacumulado/tppptodia

            else:
                tpporcentaje=0

        else:
            tpporcentaje=0


        if self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0:
            if tpacumulado!=0:
                if bussines_days.bussines_days_c!=False:
                    tptendencia=(tpacumulado/self._billed_days(options,line_id))*bussines_days.bussines_days_c

                else:
                    tptendencia=(tpacumulado/self._billed_days(options,line_id))*0


        lines.append({
        'id': 'acum',
        'name': _('') ,
        'level': 1,
        'class': 'payment',
        'columns':[
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,

        ],
        })

        lines.append({
        'id': 'acum',
        'name': _('PAPEL') ,
        'level': 2,
        'class': 'payment',
        'columns':[
                {'name':self.format_value(tpmeta), 'style': 'white-space:nowrap;'} ,
                {'name':self.format_value(tpfacturacion) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tpacumulado) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tpmeta-tpacumulado) , 'style': 'white-space:nowrap;'},
                {'name':"{:.0%}".format(tpcumplimiento), 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tppptodia) , 'style': 'white-space:nowrap;'},
                {'name':"{:.0%}".format(tpporcentaje) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tptendencia), 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tpacumuladom) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tpacumuladoy), 'style': 'white-space:nowrap;'},

        ],
        })

        tacmeta=0
        tacfacturacion=0
        taccumplimiento=0
        tacpptodia=0
        tacporcentaje=0
        tactendencia=0
        tacacumuladom=0
        tacacumuladoy=0
        bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
        tacbudget=self._get_tacbudget_goal(options,line_id)
        tacr=self._tacaccount_invoice(options,line_id)
        tacm=self._tacpayment_line(options,line_id,str(fields.Date.from_string(date_from)),str(fields.Date.from_string(date_to)))
        tacm_ant=self._tacpayment_line(options,line_id,str(fields.Date.from_string(date_from)+relativedelta(months=-1)),str(fields.Date.from_string(date_from)+timedelta(days=-1)))
        tacm_anio_ant=self._tacpayment_line(options,line_id,str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))

        if tacbudget[0]['meta'] != None:
            tacmeta=tacbudget[0]['meta']
        else:
            tacmeta=0

        if tacr[0]['residual'] != None:
            tacfacturacion=tacr[0]['residual']
        else:
            tacfacturacion=0

        if tacm[0]['monto'] != None:
            tacacumulado=tacm[0]['monto']

        else:
            tacacumulado=0

        if tacm_ant[0]['monto'] != None:
            tacacumuladom=tacm_ant[0]['monto']

        else:
            tacacumuladom=0

        if tacm_anio_ant[0]['monto'] != None:
            tacacumuladoy=tacm_anio_ant[0]['monto']
        else:
            tacacumuladoy=0


        if tacmeta!=0:
            if tacm[0]['monto']!=None:
                if tacm[0]['monto']!=0:
                    taccumplimiento=tacm[0]['monto']/tacmeta

                else:
                    taccumplimiento=0

            else:
                taccumplimiento=0

        else:
            tacumplimiento=0

        if bussines_days.bussines_days_c!=False or bussines_days.bussines_days_c!=0:
            if tacmeta!=0:
                if self._billed_days(options,line_id)!=False:
                    tacpptodia=(tacmeta/bussines_days.bussines_days_c)*self._billed_days(options,line_id)

                else:
                    tacpptodia=(tacmeta/bussines_days.bussines_days_c)*0

        if tacpptodia!=0:
            if tacacumulado!=0:
                tacporcentaje=tacacumulado/tacpptodia

            else:
                tacporcentaje=0

        else:
            tacporcentaje=0


        if self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0:
            if tacacumulado!=0:
                if bussines_days.bussines_days_c!=False:
                    tactendencia=(tacacumulado/self._billed_days(options,line_id))*bussines_days.bussines_days_c

                else:
                    tactendencia=(tacacumulado/self._billed_days(options,line_id))*0


        lines.append({
        'id': 'acum',
        'name': _('') ,
        'level': 1,
        'class': 'payment',
        'columns':[
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,

        ],
        })

        lines.append({
        'id': 'acum',
        'name': _('ARCHIMEX') ,
        'level': 2,
        'class': 'payment',
        'columns':[
                {'name':self.format_value(tacmeta), 'style': 'white-space:nowrap;'} ,
                {'name':self.format_value(tacfacturacion) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tacacumulado) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tacmeta-tacacumulado) , 'style': 'white-space:nowrap;'},
                {'name':"{:.0%}".format(taccumplimiento), 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tacpptodia) , 'style': 'white-space:nowrap;'},
                {'name':"{:.0%}".format(tacporcentaje) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tactendencia), 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tacacumuladom) , 'style': 'white-space:nowrap;'},
                {'name':self.format_value(tacacumuladoy), 'style': 'white-space:nowrap;'},

        ],
        })

        fecha=str(options['date'].get('string'))
        lines.append({
        'id': 'acum',
        'name': _('ACUMULADO ')+fecha ,
        'level': 0,
        'class': 'payment',
        'columns':[
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,

        ],
        })

        lines.append({
        'id': 'acum',
        'name': _('CORRUGADO') ,
        'level': 2,
        'class': 'payment',
        'columns':[
                {'name':self.format_value(tcacumulado) , 'style': 'white-space:nowrap;'},
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,

        ],
        })
        lines.append({
        'id': 'acum',
        'name': _('PAPEL') ,
        'level': 2,
        'class': 'payment',
        'columns':[
                {'name':self.format_value(tpacumulado) , 'style': 'white-space:nowrap;'},
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,

        ],
        })
        lines.append({
        'id': 'acum',
        'name': _('ARCHIMEX') ,
        'level': 2,
        'class': 'payment',
        'columns':[
                {'name':self.format_value(tacacumulado) , 'style': 'white-space:nowrap;'},
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,

        ],
        })

        lines.append({
        'id': 'acum',
        'name': _('TOTAL') ,
        'level': 2,
        'class': 'total',
        'columns':[
                {'name':self.format_value(tacumulado) , 'style': 'white-space:nowrap;'},
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,
                {'name':''} ,

        ],
        })







        return lines
    @api.model
    def _get_report_name(self):
        return _('Reportes de Ingresos Acumulado')
