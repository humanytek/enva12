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


class ReportsFibers(models.AbstractModel):
    _name = "reports.fibers"
    _description = "Reports Fibers"
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}

    def _get_templates(self):
        templates = super(ReportsFibers, self)._get_templates()
        templates['main_table_header_template'] = 'reports_fibers.template_reports_fibers_table_header'
        return templates

    def _get_columns_name(self, options):
        columns_header=[
        {'name': ''},
        {'name': _('VOLUMEN'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('% DE PARTICIPACION'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('VOLUMEN'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('% DE PARTICIPACION'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('VOLUMEN'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('% DE PARTICIPACION'), 'class': 'number', 'style': 'white-space:nowrap;'},
        ]


        return columns_header



    def _account_analytic_line(self,options,line_id,date_from,date_to,concepto):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        # date_from = options['date']['date_from']
        # date_to = options['date']['date_to']
        params=""
        if concepto:
            if concepto=="OCC NACIONAL":
                params = "AND (pt.default_code = 'MAP0009' OR pt.default_code = 'OCCPAC002')"
            if concepto=="DKL NACIONAL":
                params = "AND pt.default_code = 'MAP0001'"
            if concepto=="OCC IMPORTADO":
                params = "AND pt.default_code='MAP0008'"
            if concepto=="OCC ACOPIO":
                params = "AND pt.default_code='OCCPAC001'"
            if concepto=="GALLETA SIN COSTO":
                params = "AND pt.default_code='MAP0005'"
            if concepto=="DKL IMPORTADO":
                params = "AND pt.default_code='MAP0003'"
            if concepto=="GALLETA CON COSTO":
                params = "AND pt.categ_id IN (70,124,71,72)"


        # (CASE
        #     WHEN pt.default_code='MAP0003' THEN pt.default_code='DKL IMPORTADO'
        #     WHEN pt.default_code='MAP0009' THEN pt.default_code='OCC NACIONAL'
        #     WHEN pt.default_code='OCCPAC002' THEN pt.default_code='OCC NACIONAL'
        #     WHEN pt.default_code='OCCPAC001' THEN pt.default_code='OCC ACOPIO'
        #     WHEN pt.default_code='MAP0008' THEN pt.default_code='OCC IMPORTADO'
        #     WHEN pt.default_code='MAP0001' THEN pt.default_code='DKL NACIONAL'
        #     WHEN pt.default_code='MAP0005' THEN pt.default_code='GALLETA SIN COSTO'
        #     ELSE pt.default_code='MERMA (GALLETA)'
        #
        # END) as concepto,

        # AND (pt.default_code IN ('MAP0001','MAP0003','MAP0008','MAP0009','OCCPAC001','OCCPAC002','MAP0005') OR pt.categ_id IN (70,124,71,72))
        sql_query ="""
            SELECT
                    COALESCE(SUM(aal.unit_amount),0) as cantidad
                    FROM account_analytic_line aal
                    LEFT JOIN account_account aa ON aa.id=aal.general_account_id
                    LEFT JOIN product_product pp ON pp.id=aal.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    WHERE aal.date >= '"""+str(date_from)+"""' AND aal.date <= '"""+str(date_to)+"""' AND aa.code='115.03.002'
                    """+str(params)+"""

        """


        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()


        return result

    def _account_analytic_line_total(self,options,line_id,date_from,date_to):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        # date_from = options['date']['date_from']
        # date_to = options['date']['date_to']
        sql_query ="""
            SELECT

                    COALESCE(SUM(aal.unit_amount),0) as total
                    FROM account_analytic_line aal
                    LEFT JOIN account_account aa ON aa.id=aal.general_account_id
                    LEFT JOIN product_product pp ON pp.id=aal.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    WHERE aal.date >= '"""+str(date_from)+"""' AND aal.date <= '"""+str(date_to)+"""' AND aa.code='115.03.002' AND (pt.default_code IN ('MAP0001','MAP0003','MAP0008','MAP0009','OCCPAC001','OCCPAC002','MAP0005') OR pt.categ_id IN (70,124,71,72))

        """


        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()


        return result


    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        conceptos=('OCC NACIONAL','OCC IMPORTADO','OCC ACOPIO','DKL NACIONAL','DKL IMPORTADO','GALLETA CON COSTO','GALLETA SIN COSTO')
        account_analytic_line_total=self._account_analytic_line_total(options,line_id,fields.Date.from_string(date_from),fields.Date.from_string(date_to))
        account_analytic_line_total_ant=self._account_analytic_line_total(options,line_id,fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1))
        account_analytic_line_total_ant_ant=self._account_analytic_line_total(options,line_id,fields.Date.from_string(date_from)+relativedelta(months=-2),fields.Date.from_string(date_from)+relativedelta(months=-1)+timedelta(days=-1))
        lines.append({
        'id': 'fibras',
        'name': 'CONCEPTO' ,
        'level': 0,
        'class': 'concepto',
        'columns':[
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},
                {'name':''},

        ],
        })
        if conceptos:
            for c in conceptos:
                account_analytic_line=self._account_analytic_line(options,line_id,fields.Date.from_string(date_from),fields.Date.from_string(date_to),str(c))

                account_analytic_line_ant=self._account_analytic_line(options,line_id,fields.Date.from_string(date_from)+relativedelta(months=-1),fields.Date.from_string(date_from)+timedelta(days=-1),str(c))

                account_analytic_line_ant_ant=self._account_analytic_line(options,line_id,fields.Date.from_string(date_from)+relativedelta(months=-2),fields.Date.from_string(date_from)+relativedelta(months=-1)+timedelta(days=-1),str(c))

                lines.append({
                        'id': 'fibras',
                        'name': str(c) ,
                        'level': 2,
                        'class': 'fibras',
                        'columns':[
                                {'name':"{:,}".format(round((account_analytic_line[0]['cantidad']/1000)*-1)) if account_analytic_line else 0},
                                {'name':"{:.0%}".format(abs((account_analytic_line[0]['cantidad']/1000)/(account_analytic_line_total[0]['total']/1000))) if (account_analytic_line_total or account_analytic_line_total[0]['total']!=0) and (account_analytic_line or account_analytic_line[0]['cantidad']!=0) else "{:.0%}".format(0)},
                                {'name':"{:,}".format(round((account_analytic_line_ant[0]['cantidad']/1000)*-1)) if account_analytic_line_ant else 0},
                                {'name':"{:.0%}".format(abs((account_analytic_line_ant[0]['cantidad']/1000)/(account_analytic_line_total_ant[0]['total']/1000))) if (account_analytic_line_total_ant or account_analytic_line_total_ant[0]['total']!=0) and (account_analytic_line_ant or account_analytic_line_ant[0]['cantidad']!=0)  else "{:.0%}".format(0)},
                                {'name':"{:,}".format(round((account_analytic_line_ant_ant[0]['cantidad']/1000)*-1)) if account_analytic_line_ant_ant else 0},
                                {'name':"{:.0%}".format(abs((account_analytic_line_ant_ant[0]['cantidad']/1000)/(account_analytic_line_total_ant_ant[0]['total']/1000))) if (account_analytic_line_total_ant_ant or account_analytic_line_total_ant_ant[0]['total']!=0) and (account_analytic_line_ant_ant or account_analytic_line_ant_ant[0]['cantidad']!=0) else "{:.0%}".format(0)},

                        ],
                        })


        lines.append({
        'id': 'fibras',
        'name': 'TOTAL' ,
        'level': 2,
        'class': 'total',
        'columns':[
                {'name':"{:,}".format(round((account_analytic_line_total[0]['total']/1000)*-1)) if account_analytic_line_total else 0 },
                {'name':"{:.0%}".format((account_analytic_line_total[0]['total']/1000)/(account_analytic_line_total[0]['total']/1000)) if account_analytic_line_total else "{:.0%}".format(0)},
                {'name':"{:,}".format(round((account_analytic_line_total_ant[0]['total']/1000)*-1)) if account_analytic_line_total_ant else 0 },
                {'name':"{:.0%}".format((account_analytic_line_total_ant[0]['total']/1000)/(account_analytic_line_total_ant[0]['total']/1000)) if account_analytic_line_total_ant else "{:.0%}".format(0)},
                {'name':"{:,}".format(round((account_analytic_line_total_ant_ant[0]['total']/1000)*-1)) if account_analytic_line_total_ant_ant else 0 },
                {'name':"{:.0%}".format((account_analytic_line_total_ant_ant[0]['total']/1000)/(account_analytic_line_total_ant_ant[0]['total']/1000)) if account_analytic_line_total_ant_ant else "{:.0%}".format(0)},
        ],
        })
        # if account_analytic_line:
        #     for aal in account_analytic_line:
        #
        #         lines.append({
        #         'id': 'fibras',
        #         'name': str(aal['concepto']) ,
        #         'level': 2,
        #         'class': 'fibras',
        #         'columns':[
        #                 {'name':"{:,}".format(round((aal['cantidad']/1000)*-1))},
        #                 {'name':"{:.0%}".format((aal['cantidad']/1000)/(account_analytic_line_total[0]['total']/1000)) if account_analytic_line_total else "{:.0%}".format(0)},
        #
        #         ],
        #         })
        #
        #


        return lines

    @api.model
    def _get_report_name(self):
        return _('CONSUMO DE FIBRAS')
