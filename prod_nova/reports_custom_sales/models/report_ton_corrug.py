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


class ReportsTonCorrug(models.AbstractModel):
    _name = "report.ton.corrug.nova"
    _description = "Reports Sales"
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}


    def _get_columns_name(self, options):
        return [
        {'name': ''},
        {'name': _('Millares'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('Toneladas'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('$Kg'), 'class': 'number', 'style': 'white-space:nowrap;'},

        ]

    def _total_acum_line(self,options,line_id,partner):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']

        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        fecha=fields.Date.from_string(date_from)
        new_date_from:''
        if fecha.month<10:
            new_date_from=str(fecha.year)+str('-0')+str(fecha.month)+str('-01')
        else:
            new_date_from=str(fecha.year)+str('-')+str(fecha.month)+str('-01')
        new_date_to=fields.Date.from_string(new_date_from)+relativedelta(months=1)+timedelta(days=-1)
        # _logger.info('fechas ---- %s', new_date_from)
        # _logger.info('fechas dt ---- %s', new_date_to)
        if partner==True:
            sql_query ="""

                SELECT
                        SUM(ail.total_weight) as total_weight
                        FROM account_invoice_line ail
                        LEFT JOIN product_product pp ON pp.id=ail.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                        LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                        LEFT JOIN res_users rus ON rus.id=ai.user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice'
                        AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                        AND ai.date_applied >= '"""+str(new_date_from)+"""' AND ai.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND ail.uom_id not in (24,3)
                        AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                        AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.name in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.','AJEMEX S.A. DE C.V.','EMPACADORA SAN MARCOS S.A DE C.V.','PAKTON S. DE R.L. DE C.V.')



            """
        else:
            sql_query ="""

                SELECT
                        SUM(ail.total_weight) as total_weight
                        FROM account_invoice_line ail
                        LEFT JOIN product_product pp ON pp.id=ail.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                        LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                        LEFT JOIN res_users rus ON rus.id=ai.user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                        AND ai.date_applied >= '"""+str(new_date_from)+"""' AND ai.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND ail.uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.name not in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.','AJEMEX S.A. DE C.V.','EMPACADORA SAN MARCOS S.A DE C.V.','PAKTON S. DE R.L. DE C.V.')



            """

        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _total_line(self,options,line_id,partner):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        if partner==True:
            sql_query ="""

                SELECT
                        SUM(ail.total_weight) as total_weight
                        FROM account_invoice_line ail
                        LEFT JOIN product_product pp ON pp.id=ail.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                        LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                        LEFT JOIN res_users rus ON rus.id=ai.user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                        AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND ail.uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.name in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.','AJEMEX S.A. DE C.V.','EMPACADORA SAN MARCOS S.A DE C.V.','PAKTON S. DE R.L. DE C.V.')



            """
        else:
            sql_query ="""

                SELECT
                        SUM(ail.total_weight) as total_weight
                        FROM account_invoice_line ail
                        LEFT JOIN product_product pp ON pp.id=ail.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                        LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                        LEFT JOIN res_users rus ON rus.id=ai.user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                        AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND ail.uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.name not in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.','AJEMEX S.A. DE C.V.','EMPACADORA SAN MARCOS S.A DE C.V.','PAKTON S. DE R.L. DE C.V.')



            """

        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _customer_line(self,options,line_id,partner):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        if partner==True:
            sql_query ="""

                SELECT
                        ai.user_id as id_usuario,
                        rusp.name as vendedor,
                        SUM(CASE
                            WHEN ail.uom_id = 1 THEN ail.quantity/1000
                            WHEN ail.uom_id = 20 THEN ail.quantity
                        END) as cantidad,
                        SUM(ail.quantity*(ail.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=ai.date_invoice AND rcr.currency_id=ai.currency_id AND rcr.company_id=ai.company_id)))) as subtotal,
                        SUM(ail.total_weight) as total_weight
                        FROM account_invoice_line ail
                        LEFT JOIN product_product pp ON pp.id=ail.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                        LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                        LEFT JOIN res_users rus ON rus.id=ai.user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                        AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND ail.uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.name in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.','AJEMEX S.A. DE C.V.','EMPACADORA SAN MARCOS S.A DE C.V.','PAKTON S. DE R.L. DE C.V.')
                        GROUP BY rusp.name,ai.user_id
                        ORDER BY rusp.name ASC

            """
        else:
            sql_query ="""

                SELECT
                        ai.user_id as id_usuario,
                        rusp.name as vendedor,
                        SUM(CASE
                            WHEN ail.uom_id = 1 THEN ail.quantity/1000
                            WHEN ail.uom_id = 20 THEN ail.quantity
                        END) as cantidad,
                        SUM(ail.quantity*(ail.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=ai.date_invoice AND rcr.currency_id=ai.currency_id AND rcr.company_id=ai.company_id)))) as subtotal,
                        SUM(ail.total_weight) as total_weight
                        FROM account_invoice_line ail
                        LEFT JOIN product_product pp ON pp.id=ail.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                        LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                        LEFT JOIN res_users rus ON rus.id=ai.user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.type='out_invoice' AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                        AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND ail.uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.name not in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.','AJEMEX S.A. DE C.V.','EMPACADORA SAN MARCOS S.A DE C.V.','PAKTON S. DE R.L. DE C.V.')
                        GROUP BY rusp.name,ai.user_id
                        ORDER BY rusp.name ASC

            """

        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _partner_line(self,options,line_id,user_id,partner):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        if partner==True:
            sql_query ="""

                SELECT
                        rp.name as cliente,
                        ail.partner_id as id_cliente,
                        SUM(CASE
                            WHEN ail.uom_id = 1 THEN ail.quantity/1000
                            WHEN ail.uom_id = 20 THEN ail.quantity
                        END) as cantidad,
                        SUM(ail.quantity*(ail.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=ai.date_invoice AND rcr.currency_id=ai.currency_id AND rcr.company_id=ai.company_id)))) as subtotal,
                        SUM(ail.total_weight) as total_weight
                        FROM account_invoice_line ail
                        LEFT JOIN product_product pp ON pp.id=ail.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                        LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                        LEFT JOIN res_users rus ON rus.id=ai.user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.user_id = """+user_id+""" AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                        AND ai.type='out_invoice' AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND ail.uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.name in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.','AJEMEX S.A. DE C.V.','EMPACADORA SAN MARCOS S.A DE C.V.','PAKTON S. DE R.L. DE C.V.')
                        GROUP BY rp.name,ail.partner_id
                        ORDER BY rp.name ASC

            """
        else:
            sql_query ="""

                SELECT
                        rp.name as cliente,
                        ail.partner_id as id_cliente,
                        SUM(CASE
                            WHEN ail.uom_id = 1 THEN ail.quantity/1000
                            WHEN ail.uom_id = 20 THEN ail.quantity
                        END) as cantidad,
                        SUM(ail.quantity*(ail.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=ai.date_invoice AND rcr.currency_id=ai.currency_id AND rcr.company_id=ai.company_id)))) as subtotal,
                        SUM(ail.total_weight) as total_weight
                        FROM account_invoice_line ail
                        LEFT JOIN product_product pp ON pp.id=ail.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                        LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                        LEFT JOIN res_users rus ON rus.id=ai.user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE ai.state!='draft' AND ai.state!='cancel' AND ai.user_id = """+user_id+""" AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                        AND ai.type='out_invoice' AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND ail.uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.name not in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.','AJEMEX S.A. DE C.V.','EMPACADORA SAN MARCOS S.A DE C.V.','PAKTON S. DE R.L. DE C.V.')
                        GROUP BY rp.name,ail.partner_id
                        ORDER BY rp.name ASC

            """

        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _product_line(self,options,line_id,partner_id,partner):
        # tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        # if where_clause:
        #     where_clause = 'AND ' + where_clause
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)
        if partner==True:

            sql_query ="""

                SELECT
                        pp.default_code as codep,
                        pt.name as producto,
                        SUM(CASE
                            WHEN ail.uom_id = 1 THEN ail.quantity/1000
                            WHEN ail.uom_id = 20 THEN ail.quantity
                        END) as cantidad,
                        SUM(ail.quantity*(ail.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=ai.date_invoice AND rcr.currency_id=ai.currency_id AND rcr.company_id=ai.company_id)))) as subtotal,
                        SUM(ail.total_weight) as total_weight
                        FROM account_invoice_line ail
                        LEFT JOIN product_product pp ON pp.id=ail.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                        LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                        LEFT JOIN res_users rus ON rus.id=ai.user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE ai.state!='draft' AND ai.state!='cancel' AND ail.partner_id = """+partner_id+""" AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                        AND ai.type='out_invoice' AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND ail.uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.name in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.','AJEMEX S.A. DE C.V.','EMPACADORA SAN MARCOS S.A DE C.V.','PAKTON S. DE R.L. DE C.V.')
                        GROUP BY pp.default_code,pt.name
                        ORDER BY pp.default_code ASC

            """
        else:
            sql_query ="""

                SELECT
                        pp.default_code as codep,
                        pt.name as producto,
                        SUM(CASE
                            WHEN ail.uom_id = 1 THEN ail.quantity/1000
                            WHEN ail.uom_id = 20 THEN ail.quantity
                        END) as cantidad,
                        SUM(ail.quantity*(ail.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=ai.date_invoice AND rcr.currency_id=ai.currency_id AND rcr.company_id=ai.company_id)))) as subtotal,
                        SUM(ail.total_weight) as total_weight
                        FROM account_invoice_line ail
                        LEFT JOIN product_product pp ON pp.id=ail.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id
                        LEFT JOIN res_partner rp ON rp.id=ail.partner_id
                        LEFT JOIN res_users rus ON rus.id=ai.user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE ai.state!='draft' AND ai.state!='cancel' AND ail.partner_id = """+partner_id+""" AND (ai.not_accumulate=False OR ai.not_accumulate is NULL )
                        AND ai.type='out_invoice' AND ai.date_applied >= '"""+date_from+"""' AND ai.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND ail.uom_id not in (24,3)AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.name not in ('ARCHIMEX CORRUGADOS Y ETIQUETAS S.A. DE C.V.','AJEMEX S.A. DE C.V.','EMPACADORA SAN MARCOS S.A DE C.V.','PAKTON S. DE R.L. DE C.V.')
                        GROUP BY pp.default_code,pt.name
                        ORDER BY pp.default_code ASC

            """

        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        vendedores= self._customer_line(options,line_id,False)
        vendedoresa= self._customer_line(options,line_id,True)
        total_line= self._total_line(options,line_id,False)
        total_linea= self._total_line(options,line_id,True)
        total_line_month= self._total_acum_line(options,line_id,False)
        total_linea_month= self._total_acum_line(options,line_id,True)


        if vendedores:
            for v in vendedores:
                lines.append({
                'id': 'vendedor',
                'name': str(v['vendedor']) ,
                'level': 0,
                'class': 'vendedor',
                'columns':[
                        {'name':"{:,}".format(v['cantidad'])},
                        {'name':"{:,}".format(v['total_weight'])},
                        {'name':0 if v['total_weight']==0 else self.format_value(v['subtotal']/v['total_weight'])},
                ],
                })
                clientes=self._partner_line(options,line_id,str(v['id_usuario']),False)
                if clientes:
                    for c in clientes:
                        lines.append({
                        'id': 'cliente',
                        'name': str(c['cliente']) ,
                        'level': 2,
                        'class': 'vendedor',
                        'columns':[
                                {'name':"{:,}".format(c['cantidad'])},
                                {'name':"{:,}".format(c['total_weight'])},
                                {'name':0 if c['total_weight']==0 else self.format_value(c['subtotal']/c['total_weight'])},
                        ],
                        })
                        productos=self._product_line(options,line_id,str(c['id_cliente']),False)
                        if productos:
                            for p in productos:
                                lines.append({
                                'id': 'producto',
                                'name': '['+str(p['codep'])+']'+str(p['producto'][0:100]) ,
                                'level': 4,
                                'class': 'producto',
                                'columns':[
                                        {'name':"{:,}".format(p['cantidad'])},
                                        {'name':"{:,}".format(p['total_weight'])},
                                        {'name':0 if p['total_weight']==0 else self.format_value(p['subtotal']/p['total_weight'])},
                                ],
                                })



        if vendedoresa:
            for v in vendedoresa:
                lines.append({
                'id': 'vendedor',
                'name': str(v['vendedor']) ,
                'level': 0,
                'class': 'vendedor',
                'columns':[
                        {'name':"{:,}".format(v['cantidad'])},
                        {'name':"{:,}".format(v['total_weight'])},
                        {'name':0 if v['total_weight']==0 else self.format_value(v['subtotal']/v['total_weight'])},
                ],
                })
                clientes=self._partner_line(options,line_id,str(v['id_usuario']),True)
                if clientes:
                    for c in clientes:
                        lines.append({
                        'id': 'cliente',
                        'name': str(c['cliente']) ,
                        'level': 2,
                        'class': 'vendedor',
                        'columns':[
                                {'name':"{:,}".format(c['cantidad'])},
                                {'name':"{:,}".format(c['total_weight'])},
                                {'name':0 if c['total_weight']==0 else self.format_value(c['subtotal']/c['total_weight'])},
                        ],
                        })
                        productos=self._product_line(options,line_id,str(c['id_cliente']),True)
                        if productos:
                            for p in productos:
                                lines.append({
                                'id': 'producto',
                                'name': '['+str(p['codep'])+']'+str(p['producto'][0:100]) ,
                                'level': 4,
                                'class': 'producto',
                                'columns':[
                                        {'name':"{:,}".format(p['cantidad'])},
                                        {'name':"{:,}".format(p['total_weight'])},
                                        {'name':0 if p['total_weight']==0 else self.format_value(p['subtotal']/p['total_weight'])},
                                ],
                                })
        lines.append({
        'id': 'TONELAJE',
        'name': 'EMPAQUESNOVA', 'style': 'white-space:nowrap; color:#1e3c64; font-size:30px;' ,
        'level': 0,
        'class': 'vendedor',
        'columns':[
                {'name':''},
                {'name':''},
                {'name':''},
        ],
        })
        if total_line:

            for t in total_line:
                lines.append({
                'id': 'TONELAJE',
                'name': 'TONELAJE DEL DIA', 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;' ,
                'level': 2,
                'class': 'vendedor',
                'columns':[
                        {'name':''},
                        {'name':"{:,}".format(round(t['total_weight']))if t['total_weight'] else 0, 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;'},
                        {'name':''},
                ],
                })
        if total_line_month:
            for t in total_line_month:
                lines.append({
                'id': 'TONELAJE',
                'name': 'TONELAJE ACUMULADO', 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;' ,
                'level': 2,
                'class': 'vendedor',
                'columns':[
                        {'name':''},
                        {'name':"{:,}".format(round(t['total_weight']))if t['total_weight'] else 0, 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;'},
                        {'name':''},
                ],
                })
        lines.append({
        'id': 'TONELAJE',
        'name': 'ARCHIMEX', 'style': 'white-space:nowrap; color:#1e3c64; font-size:30px;' ,
        'level': 0,
        'class': 'vendedor',
        'columns':[
                {'name':''},
                {'name':''},
                {'name':''},
        ],
        })
        if total_linea:
            for ta in total_linea:
                lines.append({
                'id': 'TONELAJE',
                'name': 'TONELAJE DEL DIA',
                'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;' ,
                'level': 2,
                'class': 'vendedor',
                'columns':[
                        {'name':''},
                        {'name':"{:,}".format(round(ta['total_weight'])) if ta['total_weight'] else 0, 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;'},
                        {'name':''},
                ],
                })
        if total_linea_month:
            for ta in total_linea_month:
                lines.append({
                'id': 'TONELAJE',
                'name': 'TONELAJE ACUMULADO', 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;' ,
                'level': 2,
                'class': 'vendedor',
                'columns':[
                        {'name':''},
                        {'name':"{:,}".format(round(ta['total_weight'])) if ta['total_weight'] else 0, 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;'},
                        {'name':''},
                ],
                })




        return lines


    @api.model
    def _get_report_name(self):
        return _('Reporte de Toneladas')
