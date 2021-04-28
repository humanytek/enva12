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

    def _get_columns_name(self, options):
        return [
        {'name': ''},
        {'name': _('VOLUMEN'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('% DE PARTICIPACION'), 'class': 'number', 'style': 'white-space:nowrap;'},
        ]



    def _account_analytic_line(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        sql_query ="""
            SELECT
                    (CASE
                        WHEN pt.default_code='MAP0003' THEN 'DKL IMPORTADO'
                        WHEN pt.default_code='MAP0009' THEN 'OCC NACIONAL'
                        WHEN pt.default_code='OCCPAC002' THEN 'OCC NACIONAL'
                        WHEN pt.default_code='OCCPAC001' THEN 'OCC ACOPIO'
                        WHEN pt.default_code='MAP0008' THEN 'OCC IMPORTADO'
                        WHEN pt.default_code='MAP0001' THEN 'DKL NACIONAL'
                        WHEN pt.default_code='MAP0005' THEN 'GALLETA SIN COSTO'
                        ELSE 'MERMA (GALLETA)'

                    END) as concepto,

                    SUM(aal.unit_amount) as cantidad
                    FROM account_analytic_line aal
                    LEFT JOIN account_account aa ON aa.id=aal.general_account_id
                    LEFT JOIN product_product pp ON pp.id=aal.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    WHERE aal.date >= '"""+date_from+"""' AND aal.date <= '"""+date_to+"""' AND aa.code='115.03.002' AND (pt.default_code IN ('MAP0001','MAP0003','MAP0008','MAP0009','OCCPAC001','OCCPAC002','MAP0005') OR pt.categ_id IN (70,124,71,72))
                    GROUP BY concepto
        """


        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()


        return result

    def _account_analytic_line_total(self,options,line_id):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        sql_query ="""
            SELECT

                    COALESCE(SUM(aal.unit_amount),0) as total
                    FROM account_analytic_line aal
                    LEFT JOIN account_account aa ON aa.id=aal.general_account_id
                    LEFT JOIN product_product pp ON pp.id=aal.product_id
                    LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                    WHERE aal.date >= '"""+date_from+"""' AND aal.date <= '"""+date_to+"""' AND aa.code='115.03.002' AND (pt.default_code IN ('MAP0001','MAP0003','MAP0008','MAP0009','OCCPAC001','OCCPAC002','MAP0005') OR pt.categ_id IN (70,124,71,72))

        """


        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()


        return result


    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        account_analytic_line=self._account_analytic_line(options,line_id)
        account_analytic_line_total=self._account_analytic_line_total(options,line_id)
        lines.append({
        'id': 'fibras',
        'name': 'CONCEPTO' ,
        'level': 0,
        'class': 'concepto',
        'columns':[
                {'name':''},
                {'name':''},

        ],
        })
        if account_analytic_line:
            for aal in account_analytic_line:

                lines.append({
                'id': 'fibras',
                'name': str(aal['concepto']) ,
                'level': 2,
                'class': 'fibras',
                'columns':[
                        {'name':"{:,}".format(round((aal['cantidad']/1000)*-1))},
                        {'name':"{:.0%}".format((aal['cantidad']/1000)/(account_analytic_line_total[0]['total']/1000)) if account_analytic_line_total else "{:.0%}".format(0)},

                ],
                })

        if account_analytic_line_total:

            lines.append({
            'id': 'fibras',
            'name': 'TOTAL' ,
            'level': 2,
            'class': 'total',
            'columns':[
                    {'name':"{:,}".format(round((account_analytic_line_total[0]['total']/1000)*-1))},
                    {'name':"{:.0%}".format((account_analytic_line_total[0]['total']/1000)/(account_analytic_line_total[0]['total']/1000)) if account_analytic_line_total else "{:.0%}".format(0)},

            ],
            })


        return lines

    @api.model
    def _get_report_name(self):
        return _('CONSUMO DE FIBRAS')
