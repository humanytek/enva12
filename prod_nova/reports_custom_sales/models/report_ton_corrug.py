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

    filter_date = {'mode': 'range', 'filter': 'this_month'}


    def _get_columns_name(self, options):
        return [
        {'name': ''},
        {'name': _('Millares'), 'class': 'number', 'style': 'white-space:nowrap; font-size:20px;'},
        {'name': _('Toneladas'), 'class': 'number', 'style': 'white-space:nowrap; font-size:20px;'},
        {'name': _('$Kg'), 'class': 'number', 'style': 'white-space:nowrap; font-size:20px;'},

        ]

    def _total_acum_linep(self,options,line_id):
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
        sql_query =""" SELECT
                            SUM(aml.quantity) as cantidad
                            FROM account_move_line aml
                            LEFT JOIN product_product pp ON pp.id=aml.product_id
                            LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                            LEFT JOIN product_category pc ON pc.id=pt.categ_id
                            LEFT JOIN account_move am ON am.id=aml.move_id
                            LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                            LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                            LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                            WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                            AND aml.exclude_from_invoice_tab=False
                            AND am.date_applied >= '"""+str(new_date_from)+"""' AND am.date_applied <= '"""+date_to+"""'
                            AND pt.categ_id IN (70,71,72,124) AND aml.product_uom_id not in (1,20,24) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'

        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _total_linep(self,options,line_id):

        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)

        sql_query =""" SELECT
                            SUM(aml.quantity) as cantidad
                            FROM account_move_line aml
                            LEFT JOIN product_product pp ON pp.id=aml.product_id
                            LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                            LEFT JOIN product_category pc ON pc.id=pt.categ_id
                            LEFT JOIN account_move am ON am.id=aml.move_id
                            LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                            LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                            LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                            WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                            AND aml.exclude_from_invoice_tab=False
                            AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                            AND pt.categ_id IN (70,71,72,124) AND aml.product_uom_id not in (1,20,24) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'

        """


        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
       

        return result



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
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice'
                        AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND am.date_applied >= '"""+str(new_date_from)+"""' AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)
                        AND aml.exclude_from_invoice_tab=False
                        AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%'
                        AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.id in (SELECT pm.name FROM partner_maquila pm)



            """
        else:
            sql_query ="""

                SELECT
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND aml.exclude_from_invoice_tab=False
                        AND am.date_applied >= '"""+str(new_date_from)+"""' AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.id not in (SELECT pm.name FROM partner_maquila pm)



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
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND aml.exclude_from_invoice_tab=False
                        AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.id in (SELECT pm.name FROM partner_maquila pm)



            """
        else:
            sql_query ="""

                SELECT
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND aml.exclude_from_invoice_tab=False
                        AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.id not in (SELECT pm.name FROM partner_maquila pm)



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
                        am.invoice_user_id as id_usuario,
                        rusp.name as vendedor,
                        SUM(CASE
                            WHEN aml.product_uom_id = 1 THEN aml.quantity/1000
                            WHEN aml.product_uom_id = 20 THEN aml.quantity
                        END) as cantidad,
                        SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal,
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND aml.exclude_from_invoice_tab=False
                        AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.id in (SELECT pm.name FROM partner_maquila pm)
                        GROUP BY rusp.name,am.invoice_user_id
                        ORDER BY rusp.name ASC

            """
        else:
            sql_query ="""

                SELECT
                        am.invoice_user_id as id_usuario,
                        rusp.name as vendedor,
                        SUM(CASE
                            WHEN aml.product_uom_id = 1 THEN aml.quantity/1000
                            WHEN aml.product_uom_id = 20 THEN aml.quantity
                        END) as cantidad,
                        SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal,
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND aml.exclude_from_invoice_tab=False
                        AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.id not in (SELECT pm.name FROM partner_maquila pm)
                        GROUP BY rusp.name,am.invoice_user_id
                        ORDER BY rusp.name ASC

            """

        # params = [str(arg)] + where_params

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result
    
    def _categ_paper(self,options,line_id):
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)

        sql_query ="""
            SELECT pt.categ_id, 
            pc.name as categoria,
            SUM(aml.quantity) as cantidad,
            SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal
            FROM account_move_line aml
            LEFT JOIN product_product pp ON pp.id=aml.product_id
            LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
            LEFT JOIN product_category pc ON pc.id=pt.categ_id
            LEFT JOIN account_move am ON am.id=aml.move_id
            LEFT JOIN res_partner rp ON rp.id=aml.partner_id
            LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
            LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
            WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
            AND aml.exclude_from_invoice_tab=False
            AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
            AND pt.categ_id IN (70,71,72,124) AND aml.product_uom_id not in (1,20,24) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
            GROUP BY pt.categ_id, pc.name
            ORDER BY pc.name ASC
        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _categ_paper_partner_line(self,options,line_id,categ_id):
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)

        sql_query ="""
            SELECT 
                    rp.name as cliente,
                    aml.partner_id as id_cliente,
                    SUM(aml.quantity) as cantidad,
                    SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal
            
            FROM account_move_line aml
            LEFT JOIN product_product pp ON pp.id=aml.product_id
            LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
            LEFT JOIN product_category pc ON pc.id=pt.categ_id
            LEFT JOIN account_move am ON am.id=aml.move_id
            LEFT JOIN res_partner rp ON rp.id=aml.partner_id
            LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
            LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
            WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
            AND aml.exclude_from_invoice_tab=False
            AND pt.categ_id = """+categ_id+"""
            AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
            AND pt.categ_id IN (70,71,72,124) AND aml.product_uom_id not in (1,20,24) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
            GROUP BY rp.name,aml.partner_id
            ORDER BY rp.name ASC
        """

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _categ_paper_product_line(self,options,line_id,partner_id):
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1)

        sql_query ="""
            SELECT 
                    pp.default_code as codep,
                    pt.name as producto,
                    SUM(aml.quantity) as cantidad,
                    SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal
            
            FROM account_move_line aml
            LEFT JOIN product_product pp ON pp.id=aml.product_id
            LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
            LEFT JOIN product_category pc ON pc.id=pt.categ_id
            LEFT JOIN account_move am ON am.id=aml.move_id
            LEFT JOIN res_partner rp ON rp.id=aml.partner_id
            LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
            LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
            WHERE am.state!='draft' AND am.state!='cancel' AND am.move_type='out_invoice' AND (am.not_accumulate=False OR am.not_accumulate is NULL )
            AND aml.exclude_from_invoice_tab=False
            AND aml.partner_id = """+partner_id+"""
            AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
            AND pt.categ_id IN (70,71,72,124) AND aml.product_uom_id not in (1,20,24) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
            GROUP BY pp.default_code,pt.name
            ORDER BY pp.default_code ASC
        """

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
                        aml.partner_id as id_cliente,
                        SUM(CASE
                            WHEN aml.product_uom_id = 1 THEN aml.quantity/1000
                            WHEN aml.product_uom_id = 20 THEN aml.quantity
                        END) as cantidad,
                        SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal,
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel' AND am.invoice_user_id = """+user_id+""" AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND aml.exclude_from_invoice_tab=False
                        AND am.move_type='out_invoice' AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.id in (SELECT pm.name FROM partner_maquila pm)
                        GROUP BY rp.name,aml.partner_id
                        ORDER BY rp.name ASC

            """
        else:
            sql_query ="""

                SELECT
                        rp.name as cliente,
                        aml.partner_id as id_cliente,
                        SUM(CASE
                            WHEN aml.product_uom_id = 1 THEN aml.quantity/1000
                            WHEN aml.product_uom_id = 20 THEN aml.quantity
                        END) as cantidad,
                        SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal,
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel' AND am.invoice_user_id = """+user_id+""" AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND aml.exclude_from_invoice_tab=False
                        AND am.move_type='out_invoice' AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.id not in (SELECT pm.name FROM partner_maquila pm)
                        GROUP BY rp.name,aml.partner_id
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
                            WHEN aml.product_uom_id = 1 THEN aml.quantity/1000
                            WHEN aml.product_uom_id = 20 THEN aml.quantity
                        END) as cantidad,
                        SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal,
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel' AND aml.partner_id = """+partner_id+""" AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND aml.exclude_from_invoice_tab=False
                        AND am.move_type='out_invoice' AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3) AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.id in (SELECT pm.name FROM partner_maquila pm)
                        GROUP BY pp.default_code,pt.name
                        ORDER BY pp.default_code ASC

            """
        else:
            sql_query ="""

                SELECT
                        pp.default_code as codep,
                        pt.name as producto,
                        SUM(CASE
                            WHEN aml.product_uom_id = 1 THEN aml.quantity/1000
                            WHEN aml.product_uom_id = 20 THEN aml.quantity
                        END) as cantidad,
                        SUM(aml.quantity*(aml.price_unit*(1/(SELECT rcr.rate FROM res_currency_rate rcr WHERE rcr.name=am.invoice_date AND rcr.currency_id=am.currency_id AND rcr.company_id=am.company_id)))) as subtotal,
                        SUM(pt.weight*aml.quantity) as total_weight
                        FROM account_move_line aml
                        LEFT JOIN product_product pp ON pp.id=aml.product_id
                        LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
                        LEFT JOIN account_move am ON am.id=aml.move_id
                        LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                        LEFT JOIN res_users rus ON rus.id=am.invoice_user_id
                        LEFT JOIN res_partner rusp ON rusp.id=rus.partner_id
                        WHERE am.state!='draft' AND am.state!='cancel' AND aml.partner_id = """+partner_id+""" AND (am.not_accumulate=False OR am.not_accumulate is NULL )
                        AND aml.exclude_from_invoice_tab=False
                        AND am.move_type='out_invoice' AND am.date_applied >= '"""+date_from+"""' AND am.date_applied <= '"""+date_to+"""'
                        AND pt.categ_id IN (65,66,67,68,139,147) AND aml.product_uom_id not in (24,3)AND pt.name not ilike 'ANTICIPO DE CLIENTE%' AND pt.name not ilike 'TRANSPORTACION%' AND pt.name not ilike 'CHATARRA%' AND pt.name not ilike 'PUB GRAL VTA CHATARRA%'
                        AND rp.id not in (SELECT pm.name FROM partner_maquila pm)
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
        categ_paper= self._categ_paper(options,line_id)
        total_line= self._total_line(options,line_id,False)
        total_linea= self._total_line(options,line_id,True)
        total_line_month= self._total_acum_line(options,line_id,False)
        total_linea_month= self._total_acum_line(options,line_id,True)
        total_linep= self._total_linep(options,line_id)
        total_linep_month= self._total_acum_linep(options,line_id)

        if vendedores:
            lines.append({
                'id': 'TONELAJE',
                'name': 'CARTÓN -NOVA MÉRIDA', 
                'style': 'white-space:nowrap; color:#1e3c64; font-size:30px;' ,
                'level': 0,
                'class': 'vendedor',
                'columns':[
                        {'name':''},
                        {'name':''},
                        {'name':''},
                ],
            })
            for v in vendedores:
                lines.append({
                'id': 'vendedor',
                'name': str(v['vendedor']),
                'style': 'white-space:nowrap; color:#1e3c64; font-size:20px;',
                'level': 1,
                'class': 'vendedor',
                'columns':[
                        {'name':"{:,}".format(v['cantidad'])},
                        {'name':"{:,.3f}".format(v['total_weight']/1000)},
                        {'name':0 if v['total_weight']==0 else self.format_value(v['subtotal']/v['total_weight'])},
                ],
                })
                clientes=self._partner_line(options,line_id,str(v['id_usuario']),False)
                if clientes:
                    for c in clientes:
                        lines.append({
                        'id': 'cliente',
                        'name': str(c['cliente']) ,
                        'style': 'white-space:nowrap; color:#1e3c64; font-size:15px;',
                        'level': 2,
                        'class': 'vendedor',
                        'columns':[
                                {'name':"{:,}".format(c['cantidad'])},
                                {'name':"{:,.3f}".format(c['total_weight']/1000)},
                                {'name':0 if c['total_weight']==0 else self.format_value(c['subtotal']/c['total_weight'])},
                        ],
                        })
                        productos=self._product_line(options,line_id,str(c['id_cliente']),False)
                        if productos:
                            for p in productos:
                                lines.append({
                                'id': 'producto',
                                'name': '['+str(p['codep'])+']'+str(p['producto'][0:80]) ,
                                'style': 'white-space:nowrap; color:#1e3c64; font-size:15px;',
                                'level': 4,
                                'class': 'producto',
                                'columns':[
                                        {'name':"{:,}".format(p['cantidad'])},
                                        {'name':"{:,.3f}".format(p['total_weight']/1000)},
                                        {'name':0 if p['total_weight']==0 else self.format_value(p['subtotal']/p['total_weight'])},
                                ],
                                })



        if vendedoresa:
            lines.append({
                    'id': 'TONELAJE',
                    'name': 'CARTÓN - NOVA PUEBLA', 
                    'style': 'white-space:nowrap; color:#1e3c64; font-size:30px;' ,
                    'level': 0,
                    'class': 'vendedor',
                    'columns':[
                            {'name':''},
                            {'name':''},
                            {'name':''},
                    ],
            })
            for v in vendedoresa:
                lines.append({
                'id': 'vendedor',
                'name': str(v['vendedor']) ,
                'style': 'white-space:nowrap; color:#1e3c64; font-size:20px;',
                'level': 1,
                'class': 'vendedor',
                'columns':[
                        {'name':"{:,}".format(v['cantidad'])},
                        {'name':"{:,.3f}".format(v['total_weight']/1000)},
                        {'name':0 if v['total_weight']==0 else self.format_value(v['subtotal']/v['total_weight'])},
                ],
                })
                clientes=self._partner_line(options,line_id,str(v['id_usuario']),True)
                if clientes:
                    for c in clientes:
                        lines.append({
                        'id': 'cliente',
                        'name': str(c['cliente']) ,
                        'style': 'white-space:nowrap; color:#1e3c64; font-size:15px;',
                        'level': 2,
                        'class': 'vendedor',
                        'columns':[
                                {'name':"{:,}".format(c['cantidad'])},
                                {'name':"{:,.3f}".format(c['total_weight']/1000)},
                                {'name':0 if c['total_weight']==0 else self.format_value(c['subtotal']/c['total_weight'])},
                        ],
                        })
                        productos=self._product_line(options,line_id,str(c['id_cliente']),True)
                        if productos:
                            for p in productos:
                                lines.append({
                                'id': 'producto',
                                'name': '['+str(p['codep'])+']'+str(p['producto'][0:80]) ,
                                'style': 'white-space:nowrap; color:#1e3c64; font-size:15px;',
                                'level': 4,
                                'class': 'producto',
                                'columns':[
                                        {'name':"{:,}".format(p['cantidad'])},
                                        {'name':"{:,.3f}".format(p['total_weight']/1000)},
                                        {'name':0 if p['total_weight']==0 else self.format_value(p['subtotal']/p['total_weight'])},
                                ],
                                })
                                
        
        
        # lineas papel reporte de tonelaje
        if categ_paper:
            lines.append({
            'id': 'TONELAJE',
            'name': 'PAPEL', 'style': 'white-space:nowrap; color:#1e3c64; font-size:30px;' ,
            'level': 0,
            'class': 'vendedor',
            'columns':[
                    {'name':''},
                    {'name':''},
                    {'name':''},
            ],
            })
            for cp in categ_paper:
                lines.append({
                'id': 'vendedor',
                'name': str(cp['categoria']) ,
                'style': 'white-space:nowrap; color:#1e3c64; font-size:15px;',
                'level': 1,
                'class': 'vendedor',
                'columns':[
                        {'name':''},
                        # {'name':"{:,}".format(v['cantidad'])},
                        {'name':"{:,.3f}".format(cp['cantidad']/1000)},
                        {'name':0 if cp['cantidad']==0 else self.format_value(cp['subtotal']/cp['cantidad'])},
                ],
                })
                clientes=self._categ_paper_partner_line(options,line_id,str(cp['categ_id']))
                if clientes:
                    for c in clientes:
                        lines.append({
                        'id': 'cliente',
                        'name': str(c['cliente']) ,
                        'style': 'white-space:nowrap; color:#1e3c64; font-size:15px;',
                        'level': 2,
                        'class': 'vendedor',
                        'columns':[
                                {'name':''},
                                # {'name':"{:,}".format(c['cantidad'])},
                                {'name':"{:,.3f}".format(c['cantidad']/1000)},
                                {'name':0 if c['cantidad']==0 else self.format_value(c['subtotal']/c['cantidad'])},
                        ],
                        })
                        productos=self._categ_paper_product_line(options,line_id,str(c['id_cliente']))
                        if productos:
                            for p in productos:
                                lines.append({
                                'id': 'producto',
                                'name': '['+str(p['codep'])+']'+str(p['producto'][0:80]) ,
                                'style': 'white-space:nowrap; color:#1e3c64; font-size:15px;',
                                'level': 4,
                                'class': 'producto',
                                'columns':[
                                        {'name':''},
                                        # {'name':"{:,}".format(p['cantidad'])},
                                        {'name':"{:,.3f}".format(p['cantidad']/1000)},
                                        {'name':0 if p['cantidad']==0 else self.format_value(p['subtotal']/p['cantidad'])},
                                ],
                                })


        
        lines.append({
        'id': 'TONELAJE',
        'name': 'CARTÓN - NOVA MÉRIDA', 'style': 'white-space:nowrap; color:#1e3c64; font-size:30px;' ,
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
                        {'name':"{:,.3f}".format(t['total_weight']/1000)if t['total_weight'] else 0, 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;'},
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
                        {'name':"{:,.3f}".format(t['total_weight']/1000)if t['total_weight'] else 0, 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;'},
                        {'name':''},
                ],
                })
        lines.append({
        'id': 'TONELAJE',
        'name': 'CARTÓN - NOVA PUEBLA', 'style': 'white-space:nowrap; color:#1e3c64; font-size:30px;' ,
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
                        {'name':"{:,.3f}".format(ta['total_weight']/1000) if ta['total_weight'] else 0, 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;'},
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
                        {'name':"{:,.3f}".format(ta['total_weight']/1000) if ta['total_weight'] else 0, 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;'},
                        {'name':''},
                ],
                })

        lines.append({
        'id': 'TONELAJE',
        'name': 'PAPEL', 'style': 'white-space:nowrap; color:#1e3c64; font-size:30px;' ,
        'level': 0,
        'class': 'vendedor',
        'columns':[
                {'name':''},
                {'name':''},
                {'name':''},
        ],
        })

        if total_linep:
            for tp in total_linep:
                lines.append({
                'id': 'TONELAJE',
                'name': 'TONELAJE DEL DIA',
                'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;' ,
                'level': 2,
                'class': 'vendedor',
                'columns':[
                        {'name':''},
                        {'name':"{:,.3f}".format(tp['cantidad']/1000) if tp['cantidad'] else 0, 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;'},
                        {'name':''},
                ],
                })
        if total_linep_month:
            for tp in total_linep_month:
                lines.append({
                'id': 'TONELAJE',
                'name': 'TONELAJE ACUMULADO', 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;' ,
                'level': 2,
                'class': 'vendedor',
                'columns':[
                        {'name':''},
                        {'name':"{:,.3f}".format(tp['cantidad']/1000) if tp['cantidad'] else 0, 'style': 'white-space:nowrap; color:#1e3c64; font-size:25px;'},
                        {'name':''},
                ],
                })



        return lines


    @api.model
    def _get_report_name(self):
        return _('Reporte de Toneladas')
