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



class ReportIndicartors(models.AbstractModel):
    _name = "report.indicators.nova"
    _description = "Report Indicators"
    _inherit = 'account.report'

    filter_date = {'mode': 'single', 'filter': 'today'}

    def _get_columns(self, options):

        name_weekday = {
            0: 'LUNES',
            1: 'MARTES',
            2: 'MIERCOLES',
            3: 'JUEVES',
            4: 'VIERNES',
            5: 'SABADO',
            6: 'DOMINGO',
        }

        date_from = options['date']['date_to']
        date_to = options['date']['date_to']

        df7 = fields.Date.from_string(date_from)+timedelta(days=-6)
        df6 = fields.Date.from_string(date_from)+timedelta(days=-5)
        df5 = fields.Date.from_string(date_from)+timedelta(days=-4)
        df4 = fields.Date.from_string(date_from)+timedelta(days=-3)
        df3 = fields.Date.from_string(date_from)+timedelta(days=-2)
        df2 = fields.Date.from_string(date_from)+timedelta(days=-1)
        df = fields.Date.from_string(date_from)

        header1 = [
            {'name': _(''), 'class': 'number',
             'style': 'text-align: center; white-space:nowrap;'},
            {'name': name_weekday.get(
                df7.weekday(), "NA"), 'class': 'number', 'colspan': 1},
            {'name': name_weekday.get(
                df6.weekday(), "NA"), 'class': 'number', 'colspan': 1},
            {'name': name_weekday.get(
                df5.weekday(), "NA"), 'class': 'number', 'colspan': 1},
            {'name': name_weekday.get(
                df4.weekday(), "NA"), 'class': 'number', 'colspan': 1},
            {'name': name_weekday.get(
                df3.weekday(), "NA"), 'class': 'number', 'colspan': 1},
            {'name': name_weekday.get(
                df2.weekday(), "NA"), 'class': 'number', 'colspan': 1},
            {'name': name_weekday.get(
                df.weekday(), "NA"), 'class': 'number', 'colspan': 1},
            {'name': _('TOTAL SEMANAL'), 'class': 'number', 'colspan': 1},
            {'name': _('TOTAL ACUMULADO'), 'class': 'number', 'colspan': 1},
        ]
        header2 = [
            {'name': _(''), 'class': 'number',
             'style': 'text-align: center; white-space:nowrap;'},
            {'name': str(df7.strftime("%d/%m/%Y")),
             'class': 'number', 'style': 'white-space:nowrap;', 'colspan': 1},
            {'name': str(df6.strftime("%d/%m/%Y")),
             'class': 'number', 'style': 'white-space:nowrap;', 'colspan': 1},
            {'name': str(df5.strftime("%d/%m/%Y")),
             'class': 'number', 'style': 'white-space:nowrap;', 'colspan': 1},
            {'name': str(df4.strftime("%d/%m/%Y")),
             'class': 'number', 'style': 'white-space:nowrap;', 'colspan': 1},
            {'name': str(df3.strftime("%d/%m/%Y")),
             'class': 'number', 'style': 'white-space:nowrap;', 'colspan': 1},
            {'name': str(df2.strftime("%d/%m/%Y")),
             'class': 'number', 'style': 'white-space:nowrap;', 'colspan': 1},
            {'name': str(df.strftime("%d/%m/%Y")), 'class': 'number',
             'style': 'white-space:nowrap;', 'colspan': 1},
            {'name': '', 'class': 'number',
                'style': 'white-space:nowrap;', 'colspan': 1},
            {'name': '', 'class': 'number',
                'style': 'white-space:nowrap;', 'colspan': 1},
        ]

        return [header1, header2]
    

    def _get_indicators_line(self, options, date_from, campo):
        # date_from = options['date']['date_from']

        if campo == 'tons_lam_real':
            campo = "((coalesce (ton_lam,0) * coalesce( price_lam,0 )) * 1000) as tons_lam_real"

        elif campo == 'total':
            campo = " case when paper_weight = 0 then 0 when paper_weight > 0 then (coalesce(paca_waste,0)/coalesce(paper_weight,0)*100)  end as total"
        else:
            campo = """coalesce(""" + str(campo)+""",0) as """ + str(campo)+""

        sql_query = """select """ + \
            str(campo) + """ from indicators_nova ia where ia.indicator_date = '""" + \
            str(date_from)+"""'"""

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _get_total_indicators(self, options, date_to, date_from, campo):
        # date_from = options['date']['date_from']

        if campo == 'tons_lam_real':
            campo = "coalesce(sum(((coalesce (ton_lam,0) * coalesce( price_lam,0 )) * 1000)),0) as tons_lam_real"

        elif campo == 'price_lam':
            campo = "case when sum(coalesce (ton_lam ,0)) = 0 then 0 when sum(coalesce (ton_lam ,0)) > 0 then coalesce(sum(coalesce( price_lam,0 )) /  (sum(coalesce (ton_lam ,0)) * 1000),0) end as price_lam "
        elif campo == 'total':
            campo = "coalesce(sum((case when paper_weight = 0 then 0 when paper_weight > 0 then paca_waste/paper_weight end) * 100),0)  as total"
        else:
            campo = """coalesce(sum(coalesce(""" + str(campo) + \
                """,0)),0) as """ + str(campo)+""

        sql_query = """select """ + \
            str(campo) + """ from indicators_nova ia where ia.indicator_date >= '""" + \
            str(date_to)+"""' and ia.indicator_date <= '""" + \
            str(date_from)+"""'"""

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _get_lines_query(self, options, date_from, campo):
       # date_from = options['date']['date_from']
        sql_query = ''

        if campo == 'venta_carton':
            sql_query = """SELECT          
                    coalesce(sum(ap.amount * ap.tipocambio),0) as venta_carton
                    FROM account_payment ap
                    LEFT JOIN account_move am ON am.id = ap.move_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=ap.partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.state in ('posted','reconciled') AND ap.payment_type in ('inbound') AND rp.id is not NULL
                    AND rpc.name='CORRUGADO'
                    AND am.date = '""" + str(date_from)+"""'
                    GROUP BY am.date"""

        if campo == 'venta_papel':
            sql_query = """SELECT          
                    coalesce(sum(ap.amount * ap.tipocambio),0) as venta_papel
                    FROM account_payment ap
                    LEFT JOIN account_move am ON am.id = ap.move_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=ap.partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.state in ('posted','reconciled') AND ap.payment_type in ('inbound') AND rp.id is not NULL
                    AND rpc.name='PAPEL'
                    AND am.date = '""" + str(date_from)+"""'
                    GROUP BY am.date"""

        if campo == 'tons_carton':
            sql_query = """SELECT
                    coalesce(sum((aml.quantity*p.weight)/1000),0) as tons_carton
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id not in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date = '""" + str(date_from)+"""'
                group by aml.date"""

        if campo == 'tons_carton_real':
            sql_query = """SELECT
                    coalesce(sum(aml.credit),0) as tons_carton_real
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id not in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date = '""" + str(date_from)+"""'
                group by aml.date"""

        if campo == 'ton_puebla':
            sql_query = """SELECT
                    coalesce(sum((aml.quantity*p.weight)/1000),0) as ton_puebla
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date = '""" + str(date_from)+"""'
                group by aml.date"""

        if campo == 'ton_puebla_real':
            sql_query = """SELECT
                    coalesce(sum(aml.credit),0) as ton_puebla_real
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date = '""" + str(date_from)+"""'
                group by aml.date"""

        if campo == 'tons_papel':
            sql_query = """SELECT
                    coalesce(sum((aml.quantity/1000)),0) as tons_papel
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
             WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (70,124,71,72) and aml.product_uom_id not in (24) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                AND aml.date = '""" + str(date_from)+"""'
                group by aml.date"""

        if campo == 'tons_papel_real':
            sql_query = """SELECT
                    coalesce(sum( aml.credit ),0) as tons_papel_real
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (70,124,71,72) and aml.product_uom_id not in (24) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                AND aml.date = '""" + str(date_from)+"""'
                group by aml.date"""

        if campo == 'kg_carton':
            sql_query = """SELECT
                    coalesce((sum(aml.credit)/sum(aml.quantity*p.weight)),0) as kg_carton
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id not in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date = '""" + str(date_from)+"""'
                group by aml.date"""

        if campo == 'kg_puebla':
            sql_query = """SELECT
                    coalesce((sum(aml.credit)/sum(aml.quantity*p.weight)),0) as kg_puebla
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date = '""" + str(date_from)+"""'
                group by aml.date"""


        if campo == 'kg_papel':
            sql_query = """SELECT
                    coalesce((sum(aml.credit)/sum(aml.quantity)),0) as kg_papel
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (70,124,71,72) and aml.product_uom_id not in (24) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                AND aml.date = '""" + str(date_from)+"""'
                group by aml.date"""

        if campo == 'cartera':
            sql_query = """SELECT COALESCE(SUM(results.balance),0) as cartera
                FROM (
                    SELECT COALESCE(SUM((acl.balance * -1)),0) as balance
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_partner rp on rp.id=acl.partner_id   
                WHERE aa.code in ('102.01.120','102.01.140','102.01.160','102.01.170','103.01.001','103.01.002') AND debit = 0 AND credit > 0
                and acl.date = '""" + str(date_from)+"""'
                AND (acl.partner_id is not Null )
                AND (acl.partner_id != 1)
                AND (acl.partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=acl.partner_id LIMIT 1))
                and acl.parent_state = 'posted'
                and acl.term_payment_nova = 'credito'
                and acl.is_project is not true
                union
                SELECT COALESCE(SUM((acl.amount_currency  * -1)),0) * (1/coalesce(usd.rate,1)) as balance
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_partner rp on rp.id=acl.partner_id   
                LEFT JOIN res_currency_rate usd on usd.name = '""" + str(date_from)+"""' and usd.currency_id = 2
                WHERE aa.code in ('102.01.270','102.01.220') AND debit = 0 AND credit > 0
                and acl.date = '""" + str(date_from)+"""'
                AND (acl.partner_id is not Null )
                AND (acl.partner_id != 1)
                AND (acl.partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=acl.partner_id LIMIT 1))
                and acl.parent_state = 'posted'
                and acl.term_payment_nova = 'credito'
                and acl.is_project is not true
                group by usd.rate
                union
                SELECT COALESCE(SUM((acl.amount_currency * -1 )),0) * (1/coalesce(euro.rate,1)) as balance
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_partner rp on rp.id=acl.partner_id   
                LEFT JOIN res_currency_rate euro on euro.name = '""" + str(date_from)+"""' and euro.currency_id = 1
                WHERE aa.code in ('102.01.370','102.01.350','102.01.320') AND debit = 0 AND credit > 0
                and acl.date = '""" + str(date_from)+"""'
                AND (acl.partner_id is not Null )
                AND (acl.partner_id != 1)
                AND (acl.partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=acl.partner_id LIMIT 1))
                and acl.parent_state = 'posted'
                and acl.term_payment_nova = 'credito'
                and acl.is_project is not true
                group by euro.rate ) AS results """
                
        if campo == 'contado':
            sql_query = """SELECT COALESCE(SUM(results.balance),0) as contado
                FROM (
                    SELECT COALESCE(SUM((acl.balance * -1)),0) as balance
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_partner rp on rp.id=acl.partner_id   
                WHERE aa.code in ('102.01.120','102.01.140','102.01.160','102.01.170','103.01.001','103.01.002') AND debit = 0 AND credit > 0
                and acl.date = '""" + str(date_from)+"""'
                AND (acl.partner_id is not Null )
                AND (acl.partner_id != 1)
                AND (acl.partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=acl.partner_id LIMIT 1))
                and acl.parent_state = 'posted'
                and acl.term_payment_nova = 'contado'
                and acl.is_project is not true
                union
                SELECT COALESCE(SUM((acl.amount_currency  * -1)),0) * (1/coalesce(usd.rate,1)) as balance
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_partner rp on rp.id=acl.partner_id   
                LEFT JOIN res_currency_rate usd on usd.name = '""" + str(date_from)+"""' and usd.currency_id = 2
                WHERE aa.code in ('102.01.270','102.01.220') AND debit = 0 AND credit > 0
                and acl.date = '""" + str(date_from)+"""'
                AND (acl.partner_id is not Null )
                AND (acl.partner_id != 1)
                AND (acl.partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=acl.partner_id LIMIT 1))
                and acl.parent_state = 'posted'
                and acl.term_payment_nova = 'contado'
                and acl.is_project is not true
                group by usd.rate
                union
                SELECT COALESCE(SUM((acl.amount_currency * -1 )),0) * (1/coalesce(euro.rate,1)) as balance
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_partner rp on rp.id=acl.partner_id   
                LEFT JOIN res_currency_rate euro on euro.name = '""" + str(date_from)+"""' and euro.currency_id = 1
                WHERE aa.code in ('102.01.370','102.01.350','102.01.320') AND debit = 0 AND credit > 0
                and acl.date = '""" + str(date_from)+"""'
                AND (acl.partner_id is not Null )
                AND (acl.partner_id != 1)
                AND (acl.partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=acl.partner_id LIMIT 1))
                and acl.parent_state = 'posted'
                and acl.term_payment_nova = 'contado'
                and acl.is_project is not true
                group by euro.rate ) AS results """
        if campo == 'project':
            sql_query = """SELECT COALESCE(SUM(results.balance),0) as project
                FROM (
                    SELECT COALESCE(SUM((acl.balance * -1)),0) as balance
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_partner rp on rp.id=acl.partner_id   
                WHERE aa.code in ('102.01.120','102.01.140','102.01.160','102.01.170','103.01.001','103.01.002') AND debit = 0 AND credit > 0
                and acl.date = '""" + str(date_from)+"""'
                AND (acl.partner_id is not Null )
                AND (acl.partner_id != 1)
                AND (acl.partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=acl.partner_id LIMIT 1))
                and acl.parent_state = 'posted'
                and acl.is_project is  true
                union
                SELECT COALESCE(SUM((acl.amount_currency  * -1)),0) * (1/coalesce(usd.rate,1)) as balance
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_partner rp on rp.id=acl.partner_id   
                LEFT JOIN res_currency_rate usd on usd.name = '""" + str(date_from)+"""' and usd.currency_id = 2
                WHERE aa.code in ('102.01.270','102.01.220') AND debit = 0 AND credit > 0
                and acl.date = '""" + str(date_from)+"""'
                AND (acl.partner_id is not Null )
                AND (acl.partner_id != 1)
                AND (acl.partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=acl.partner_id LIMIT 1))
                and acl.parent_state = 'posted'
                and acl.is_project is  true
                group by usd.rate
                union
                SELECT COALESCE(SUM((acl.amount_currency * -1 )),0) * (1/coalesce(euro.rate,1)) as balance
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_partner rp on rp.id=acl.partner_id   
                LEFT JOIN res_currency_rate euro on euro.name = '""" + str(date_from)+"""' and euro.currency_id = 1
                WHERE aa.code in ('102.01.370','102.01.350','102.01.320') AND debit = 0 AND credit > 0
                and acl.date = '""" + str(date_from)+"""'
                AND (acl.partner_id is not Null )
                AND (acl.partner_id != 1)
                AND (acl.partner_id NOT IN (SELECT partner_id FROM res_partner_category rpc left join res_partner_res_partner_category_rel rpcr ON rpcr.category_id = rpc.id WHERE rpc.name='BANCO' AND rpcr.partner_id=acl.partner_id LIMIT 1))
                and acl.parent_state = 'posted'
                and acl.is_project is  true
                group by euro.rate ) AS results """
        if campo == 'dolar':
            sql_query = """
                SELECT  COALESCE(SUM(acl.amount_currency),0) * (1/coalesce(usd.rate,1)) as dolar
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_currency_rate usd on usd.name = '""" + str(date_from)+"""' and usd.currency_id = 2
                WHERE aa.code in ('102.01.270','102.01.220') and acl.date <='""" + str(date_from)+"""' and acl.parent_state = 'posted'
                group by usd.rate"""
        if campo == 'euro':
            sql_query = """
                SELECT  COALESCE(SUM(acl.amount_currency),0) * (1/coalesce(euro.rate,1)) as euro
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                LEFT JOIN res_currency_rate euro on euro.name = '""" + str(date_from)+"""' and euro.currency_id = 1
                WHERE aa.code in ('102.01.370','102.01.350','102.01.320') and acl.date <='""" + str(date_from)+"""' and acl.parent_state = 'posted'
                group by euro.rate"""
        if campo == 'mxn':
            sql_query = """
                SELECT  COALESCE(SUM(acl.balance),0) as mxn
                FROM account_move_line acl
                LEFT JOIN account_account on account_account.id=acl.account_id
                WHERE account_account.code in ('102.01.120','102.01.140','102.01.160','102.01.170','103.01.001','103.01.002')
                and acl.date <= '""" + str(date_from)+"""'  and acl.parent_state = 'posted'"""

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    def _get_total_query(self, options, date_to, date_from, campo):
       # date_from = options['date']['date_from']
        sql_query = ''

        if campo == 'venta_carton':
            sql_query = """SELECT          
                    coalesce(sum(ap.amount * ap.tipocambio),0) as venta_carton
                    FROM account_payment ap
                    LEFT JOIN account_move am ON am.id = ap.move_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=ap.partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.state in ('posted','reconciled') AND ap.payment_type in ('inbound') AND rp.id is not NULL
                    AND rpc.name='CORRUGADO'
                    AND am.date >= '""" + str(date_to)+"""' and am.date <= '""" + str(date_from)+"""'"""

        if campo == 'venta_papel':
            sql_query = """SELECT          
                    coalesce(sum(ap.amount * ap.tipocambio),0) as venta_papel
                    FROM account_payment ap
                    LEFT JOIN account_move am ON am.id = ap.move_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    LEFT JOIN res_partner_res_partner_category_rel rpcr ON rpcr.partner_id=ap.partner_id
                    LEFT JOIN res_partner_category rpc ON rpc.id=rpcr.category_id
                    WHERE am.state in ('posted','reconciled') AND ap.payment_type in ('inbound') AND rp.id is not NULL
                    AND rpc.name='PAPEL'
                    AND am.date >= '""" + str(date_to)+"""' and am.date <= '""" + str(date_from)+"""'"""

        if campo == 'tons_carton':
            sql_query = """SELECT
                    coalesce(sum((aml.quantity*p.weight)/1000),0) as tons_carton
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id not in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'tons_carton_real':
            sql_query = """SELECT
                    coalesce(sum(aml.credit),0) as tons_carton_real
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id not in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'ton_puebla':
            sql_query = """SELECT
                    coalesce(sum((aml.quantity*p.weight)/1000),0) as ton_puebla
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'ton_puebla_real':
            sql_query = """SELECT
                    coalesce(sum(aml.credit),0) as ton_puebla_real
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'tons_papel':
            sql_query = """SELECT
                    coalesce(sum((aml.quantity/1000)),0) as tons_papel
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
             WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (70,124,71,72) and aml.product_uom_id not in (24) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'tons_papel_real':
            sql_query = """SELECT
                    coalesce(sum( aml.credit ),0) as tons_papel_real
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (70,124,71,72) and aml.product_uom_id not in (24) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'kg_carton':
            sql_query = """select case when sum(coalesce(aml.credit,0)) = 0 then 0 
                           when  sum(coalesce(aml.credit,0))  > 0  then coalesce(sum(aml.credit)/sum(aml.quantity*p.weight),0) end as kg_carton
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id not in (SELECT pm.name FROM partner_maquila pm)
               AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'kg_puebla':
            sql_query = """select case when sum(coalesce(aml.credit,0)) = 0 then 0 
                           when  sum(coalesce(aml.credit,0))  > 0  then coalesce(sum(aml.credit)/sum(aml.quantity*p.weight),0) end as kg_puebla
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (65,66,67,68,139,147) and aml.product_uom_id not in (24,3) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                and partner.id in (SELECT pm.name FROM partner_maquila pm)
                AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'kg_papel':
            sql_query = """select case when sum(coalesce(aml.credit,0)) = 0 then 0 
                           when  sum(coalesce(aml.credit,0))  > 0  then coalesce(sum(aml.credit)/sum(aml.quantity),0) end as kg_papel
                    FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join res_partner rusp ON rusp.id=customer.id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
            WHERE
                aml.exclude_from_invoice_tab = False and am.move_type in ('out_invoice') and aml.parent_state='posted'
                and am.state!='draft' AND am.state!='cancel' and (am.not_accumulate=False OR am.not_accumulate is NULL )
                and t.categ_id IN (70,124,71,72) and aml.product_uom_id not in (24) 
                and t.name not ilike 'ANTICIPO DE CLIENTE%' and t.name not ilike 'TRANSPORTACION%' 
                and t.name not ilike 'CHATARRA%' and t.name not ilike 'PUB GRAL VTA CHATARRA%'
                AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'cartera':
            sql_query = """ SELECT
                    coalesce(sum(ap.amount * ap.tipocambio),0) as cartera
                    FROM account_payment ap
                    LEFT JOIN account_move aml ON aml.id = ap.move_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    WHERE aml.state in ('posted')  
                    and ap.partner_type ='supplier' and ap.is_internal_transfer = false
                    AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'contado':
            sql_query = """ SELECT
                    coalesce(sum(ap.amount * ap.tipocambio),0) as contado
                    FROM account_payment ap
                    LEFT JOIN account_move aml ON aml.id = ap.move_id
                    LEFT JOIN res_partner rp ON rp.id=ap.partner_id
                    WHERE aml.state in ('posted')  
                    and ap.partner_type ='supplier' and ap.is_internal_transfer = false
                    AND aml.date >= '""" + str(date_to)+"""' and aml.date <= '""" + str(date_from)+"""'"""

        if campo == 'saldo':
            sql_query = """
            SELECT COALESCE(SUM(acl.amount_currency),0) as saldo
                FROM account_move_line acl
                LEFT JOIN account_account aa on aa.id=acl.account_id
                WHERE aa.code in ('102.01.270','102.01.220') and acl.date <='""" + str(date_from)+"""'"""

        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()

        return result

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        header = [{'name': 'BACK ORDER SIN CORRUGAR', 'cantidad': 'si', 'campo': 'back_order', 'bandera': 0}, {'name': 'BACK LOG (ATRASOS)', 'cantidad': 'si', 'campo': 'back_log', 'bandera': 0}, {'name': 'CORRUGADORA FOSBER', 'cantidad': 'no', 'bandera': 0},
                  {'name': 'CONVERSION (FLEXO)', 'cantidad': 'no', 'bandera': 0}, {'name': 'INVENTARIO (FINAL)', 'cantidad': 'no', 'bandera': 0}, {
            'name': 'EMBARQUES', 'cantidad': 'no', 'bandera': 0}, {'name': 'SALDO BANCARIO', 'cantidad': 'si', 'campo': 'saldo', 'bandera': 1},
            {'name': 'COBRANZA', 'cantidad': 'no', 'bandera': 0}, {'name': 'PAGOS', 'cantidad': 'no', 'bandera': 0}, {'name': 'PRECIO PROMEDIO', 'cantidad': 'no', 'bandera': 0}]
        subheading = [{'header': 'CORRUGADORA FOSBER', 'subheader': 'Toneladas', 'campo': 'ton_fosber', 'bandera': 0}, {'header': 'CORRUGADORA FOSBER', 'subheader': 'Mezcla Promedio', 'campo': 'mezcla_prom', 'bandera': 0},
                      {'header': 'CORRUGADORA FOSBER', 'subheader': 'Papel Consumido Pesado', 'campo': 'paper_weight', 'bandera': 0}, {
                          'header': 'CORRUGADORA FOSBER', 'subheader': 'Papel Consumido', 'campo': 'paper_weight', 'bandera': 0},
                      {'header': 'CORRUGADORA FOSBER', 'subheader': 'Trim Controlable', 'campo': 'controllable_trim', 'bandera': 0}, {
                          'header': 'CONVERSION (FLEXO)', 'subheader': 'Terminado al Almacén', 'campo': 'finished_warehouse', 'bandera': 0},
                      {'header': 'CONVERSION (FLEXO)', 'subheader': '% Total de Desperdicio Planta', 'campo': 'total_waste', 'bandera': 0}, {
            'header': 'CONVERSION (FLEXO)', 'subheader': 'Desperdicio Pacas', 'campo': 'paca_waste', 'bandera': 0},
            {'header': 'CONVERSION (FLEXO)', 'subheader': '% Total de Desperdicio Planta Fórmula', 'campo': 'total', 'bandera': 0}, {
            'header': 'INVENTARIO (FINAL)', 'subheader': 'Papel (Toneladas)', 'campo': 'tons_paper', 'bandera': 0},
            {'header': 'INVENTARIO (FINAL)', 'subheader': 'Total Rollos', 'campo': 'total_rolls', 'bandera': 0}, {
            'header': 'EMBARQUES', 'subheader': 'Toneladas', 'campo': 'tons_shipment', 'bandera': 0},
            {'header': 'EMBARQUES', 'subheader': 'Toneladas Facturadas Cartón', 'campo': 'tons_carton', 'bandera': 1}, {
                          'header': 'EMBARQUES', 'subheader': 'Facturación Real Cartón', 'campo': 'tons_carton_real', 'bandera': 1},
            {'header': 'EMBARQUES', 'subheader': 'Toneladas Facturadas Lámina', 'campo': 'ton_lam', 'bandera': 0}, {
                          'header': 'EMBARQUES', 'subheader': 'Facturación Real Lámina', 'campo': 'tons_lam_real', 'bandera': 0},
            {'header': 'EMBARQUES', 'subheader': 'Toneladas Facturadas Venta Directa Puebla', 'campo': 'ton_puebla', 'bandera': 1}, {
                          'header': 'EMBARQUES', 'subheader': 'Facturación Real Venta Directa Puebla', 'campo': 'ton_puebla_real', 'bandera': 1},
            {'header': 'EMBARQUES', 'subheader': 'Toneladas Facturadas Papel', 'campo': 'tons_papel', 'bandera': 1}, {
                          'header': 'EMBARQUES', 'subheader': 'Facturación Real Papel', 'campo': 'tons_papel_real', 'bandera': 1},
            {'header': 'COBRANZA', 'subheader': 'Venta de Cartón', 'campo': 'venta_carton', 'bandera': 1}, {
                          'header': 'COBRANZA', 'subheader': 'Venta de Papel', 'campo': 'venta_papel', 'bandera': 1},
            {'header': 'COBRANZA', 'subheader': 'Otros Ingresos',
                'campo': 'other_receipts', 'bandera': 0},
            {'header': 'COBRANZA', 'subheader': 'Total Cobranza', 'campo': 'total_cobranza', 'bandera': 1}, {
                          'header': 'PAGOS', 'subheader': 'Contado', 'campo': 'contado', 'bandera': 1},
            {'header': 'PAGOS', 'subheader': 'Cartera', 'campo': 'cartera', 'bandera': 1}, {
                          'header': 'PAGOS', 'subheader': 'Proyecto', 'campo': 'project', 'bandera': 1},
            {'header': 'PAGOS', 'subheader': 'Total Pagos',
                'campo': 'total_pagos', 'bandera': 1},
            {'header': 'PRECIO PROMEDIO', 'subheader': 'Precio Promedio Venta por Kilo Cartón', 'campo': 'kg_carton', 'bandera': 1}, {
            'header': 'PRECIO PROMEDIO', 'subheader': 'Precio Promedio Venta por Kilo Lámina', 'campo': 'price_lam', 'bandera': 0},
            {'header': 'PRECIO PROMEDIO', 'subheader': 'Precio Promedio Venta por Kilo Venta Directa Puebla', 'campo': 'kg_puebla', 'bandera': 1}, {'header': 'PRECIO PROMEDIO', 'subheader': 'Precio Promedio Venta por Kilo Papelera', 'campo': 'kg_papel', 'bandera': 1}]

        date_from = options['date']['date_to']
        df7 = fields.Date.from_string(date_from)+timedelta(days=-6)
        df6 = fields.Date.from_string(date_from)+timedelta(days=-5)
        df5 = fields.Date.from_string(date_from)+timedelta(days=-4)
        df4 = fields.Date.from_string(date_from)+timedelta(days=-3)
        df3 = fields.Date.from_string(date_from)+timedelta(days=-2)
        df2 = fields.Date.from_string(date_from)+timedelta(days=-1)
        df = fields.Date.from_string(date_from)
        if df.month < 10:
            new_date_from = str(df.year)+str('-0')+str(df.month)+str('-01')
        else:
            new_date_from = str(df.year)+str('-')+str(df.month)+str('-01')
        totalsemana = 0
        for h in header:
            if (h['cantidad'] == 'si'):

                if (h['bandera'] == 0):
                    indicator = self._get_indicators_line(
                        options, df, str(h['campo']))
                    indicator2 = self._get_indicators_line(
                        options, df2, str(h['campo']))
                    indicator3 = self._get_indicators_line(
                        options, df3, str(h['campo']))
                    indicator4 = self._get_indicators_line(
                        options, df4, str(h['campo']))
                    indicator5 = self._get_indicators_line(
                        options, df5, str(h['campo']))
                    indicator6 = self._get_indicators_line(
                        options, df6, str(h['campo']))
                    indicator7 = self._get_indicators_line(
                        options, df7, str(h['campo']))
                    total_month = self._get_total_indicators(
                        options, new_date_from, df, str(h['campo']))
                    totalsemana = (indicator[0][h['campo']] if indicator else 0) + (indicator2[0][h['campo']] if indicator2 else 0) + (indicator3[0][h['campo']] if indicator3 else 0) + (
                        indicator4[0][h['campo']] if indicator4 else 0) + (indicator5[0][h['campo']] if indicator5 else 0) + (indicator6[0][h['campo']] if indicator6 else 0) + (indicator7[0][h['campo']] if indicator7 else 0)

                    lines.append({
                        'id': 'fibras',
                        'name': str(h['name']),
                        'level': 0,
                        'class': 'concepto',
                        'columns': [
                            {'name': "{:,.3f}".format(
                                indicator7[0][h['campo']]) if indicator7 else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(round(
                                indicator6[0][h['campo']]), 3) if indicator6 else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(
                                indicator5[0][h['campo']]) if indicator5 else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(
                                indicator4[0][h['campo']]) if indicator4 else "{:,.3f}".format(0)},
                            {'name': "{:,.3f}".format(
                                indicator3[0][h['campo']]) if indicator3 else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(
                                indicator2[0][h['campo']]) if indicator2 else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(
                                indicator[0][h['campo']]) if indicator else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(totalsemana)},
                            {'name': "{:,.3f}".format(
                                total_month[0][h['campo']]) if total_month else "{:,.3f}".format(0)},
                        ],
                    })
                else:
                    indicator = []
                    indicator2 = []
                    indicator3 = []
                    indicator4 = []
                    indicator5 = []
                    indicator6 = []
                    indicator7 = []
                    dolar = self._get_lines_query(options, df, str('dolar'))
                    euro = self._get_lines_query(options, df, str('euro'))
                    mxn = self._get_lines_query(options, df, str('mxn'))
                    indicator.append({'saldo': (dolar[0]['dolar'] if dolar else 0) + (
                        euro[0]['euro'] if euro else 0) + (mxn[0]['mxn'] if mxn else 0)})

                    dolar2 = self._get_lines_query(options, df2, str('dolar'))
                    euro2 = self._get_lines_query(options, df2, str('euro'))
                    mxn2 = self._get_lines_query(options, df2, str('mxn'))
                    indicator2.append({'saldo': (dolar2[0]['dolar'] if dolar2 else 0) + (
                        euro2[0]['euro'] if euro2 else 0) + (mxn2[0]['mxn'] if mxn2 else 0)})

                    dolar3 = self._get_lines_query(options, df3, str('dolar'))
                    euro3 = self._get_lines_query(options, df3, str('euro'))
                    mxn3 = self._get_lines_query(options, df3, str('mxn'))
                    indicator3.append({'saldo': (dolar3[0]['dolar'] if dolar3 else 0) + (
                        euro3[0]['euro'] if euro3 else 0) + (mxn3[0]['mxn'] if mxn3 else 0)})

                    dolar4 = self._get_lines_query(options, df4, str('dolar'))
                    euro4 = self._get_lines_query(options, df4, str('euro'))
                    mxn4 = self._get_lines_query(options, df4, str('mxn'))
                    indicator4.append({'saldo': (dolar4[0]['dolar'] if dolar4 else 0) + (
                        euro4[0]['euro'] if euro4 else 0) + (mxn4[0]['mxn'] if mxn4 else 0)})

                    dolar5 = self._get_lines_query(options, df5, str('dolar'))
                    euro5 = self._get_lines_query(options, df5, str('euro'))
                    mxn5 = self._get_lines_query(options, df5, str('mxn'))
                    indicator5.append({'saldo': (dolar5[0]['dolar'] if dolar2 else 0) + (
                        euro5[0]['euro'] if euro5 else 0) + (mxn5[0]['mxn'] if mxn5 else 0)})

                    dolar6 = self._get_lines_query(options, df6, str('dolar'))
                    euro6 = self._get_lines_query(options, df6, str('euro'))
                    mxn6 = self._get_lines_query(options, df6, str('mxn'))
                    indicator6.append({'saldo': (dolar6[0]['dolar'] if dolar6 else 0) + (
                        euro6[0]['euro'] if euro6 else 0) + (mxn6[0]['mxn'] if mxn6 else 0)})

                    dolar7 = self._get_lines_query(options, df7, str('dolar'))
                    euro7 = self._get_lines_query(options, df7, str('euro'))
                    mxn7 = self._get_lines_query(options, df7, str('mxn'))
                    indicator7.append({'saldo': (dolar7[0]['dolar'] if dolar7 else 0) + (
                        euro7[0]['euro'] if euro7 else 0) + (mxn7[0]['mxn'] if mxn7 else 0)})

                 #   total_month = self._get_total_query(options,new_date_from, df,str(h['campo']))
                    date_initial = datetime.fromisoformat(new_date_from)
                    diferencia = df - date_initial.date()
                    iterator = 0
                    total = 0
                    while (iterator < (diferencia.days + 1)):
                        dolar = self._get_lines_query(options, fields.Date.from_string(
                            date_initial.date())+timedelta(days=iterator), str('dolar'))
                        euro = self._get_lines_query(options, fields.Date.from_string(
                            date_initial.date())+timedelta(days=iterator), str('euro'))
                        mxn = self._get_lines_query(options, fields.Date.from_string(
                            date_initial.date())+timedelta(days=iterator), str('mxn'))
                        total = total + (dolar[0]['dolar'] if dolar else 0) + (
                            euro[0]['euro'] if euro else 0) + (mxn[0]['mxn'] if mxn else 0)
                        iterator = iterator + 1

                    total_month = total / iterator
                    totalsemana = ((indicator[0][h['campo']] if indicator else 0) + (indicator2[0][h['campo']] if indicator2 else 0) + (indicator3[0][h['campo']] if indicator3 else 0) + (
                        indicator4[0][h['campo']] if indicator4 else 0) + (indicator5[0][h['campo']] if indicator5 else 0) + (indicator6[0][h['campo']] if indicator6 else 0) + (indicator7[0][h['campo']] if indicator7 else 0))/7

                    lines.append({
                        'id': 'fibras',
                        'name': str(h['name']),
                        'level': 0,
                        'class': 'concepto',
                        'columns': [
                            {'name': "{:,.3f}".format(
                                indicator7[0][h['campo']]) if indicator7 else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(round(
                                indicator6[0][h['campo']]), 3) if indicator6 else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(
                                indicator5[0][h['campo']]) if indicator5 else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(
                                indicator4[0][h['campo']]) if indicator4 else "{:,.3f}".format(0)},
                            {'name': "{:,.3f}".format(
                                indicator3[0][h['campo']]) if indicator3 else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(
                                indicator2[0][h['campo']]) if indicator2 else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(
                                indicator[0][h['campo']]) if indicator else "{:,.3f}".format(0)},
                            {'name':  "{:,.3f}".format(totalsemana)},
                            {'name': "{:,.3f}".format(total_month)},
                        ]
                    })

            else:
                lines.append({
                    'id': 'fibras',
                    'name': str(h['name']),
                    'level': 0,
                    'class': 'concepto',
                    'columns': [
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                    ],
                })

                for s in subheading:
                    if (s['header'] == h['name']):
                        if (s['bandera'] == 0):
                            indicator = self._get_indicators_line(
                                options, df, str(s['campo']))
                            indicator2 = self._get_indicators_line(
                                options, df2, str(s['campo']))
                            indicator3 = self._get_indicators_line(
                                options, df3, str(s['campo']))
                            indicator4 = self._get_indicators_line(
                                options, df4, str(s['campo']))
                            indicator5 = self._get_indicators_line(
                                options, df5, str(s['campo']))
                            indicator6 = self._get_indicators_line(
                                options, df6, str(s['campo']))
                            indicator7 = self._get_indicators_line(
                                options, df7, str(s['campo']))
                            total_month = self._get_total_indicators(
                                options, new_date_from, df, str(s['campo']))

                            totalsemana = (indicator[0][s['campo']] if indicator else 0) + (indicator2[0][s['campo']] if indicator2 else 0) + (indicator3[0][s['campo']] if indicator3 else 0) + (
                                indicator4[0][s['campo']] if indicator4 else 0) + (indicator5[0][s['campo']] if indicator5 else 0) + (indicator6[0][s['campo']] if indicator6 else 0) + (indicator7[0][s['campo']] if indicator7 else 0)

                            if totalsemana is None:
                                totalsemana = 0
                            if total_month[0][s['campo']] is None:
                                total_month[0][s['campo']] = 0
                            lines.append({
                                'id': 'fibras',
                                'name': str(s['subheader']),
                                'level': 2,
                                'class': 'concepto',
                                'columns': [
                                    {'name': "{:,.3f}".format(
                                        indicator7[0][s['campo']]) if indicator7 else "{:,.3f}".format(0)},
                                    {'name': "{:,.3f}".format(
                                        indicator6[0][s['campo']]) if indicator6 else "{:,.3f}".format(0)},
                                    {'name': "{:,.3f}".format(
                                        indicator5[0][s['campo']]) if indicator5 else "{:,.3f}".format(0)},
                                    {'name': "{:,.3f}".format(
                                        indicator4[0][s['campo']]) if indicator4 else "{:,.3f}".format(0)},
                                    {'name': "{:,.3f}".format(
                                        indicator3[0][s['campo']]) if indicator3 else "{:,.3f}".format(0)},
                                    {'name': "{:,.3f}".format(
                                        indicator2[0][s['campo']]) if indicator2 else "{:,.3f}".format(0)},
                                    {'name': "{:,.3f}".format(
                                        indicator[0][s['campo']]) if indicator else "{:,.3f}".format(0)},
                                    {'name': "{:,.3f}".format(totalsemana)},
                                    {'name': "{:,.3f}".format(
                                        total_month[0][s['campo']]) if total_month else "{:,.3f}".format(0)},
                                ],
                            })
                        else:
                            if s['campo'] == 'saldo':
                                lines.append({
                                    'id': 'fibras',
                                    'name': str(s['subheader']),
                                    'level': 2,
                                    'class': 'concepto',
                                    'columns': [
                                        {'name': 0.000},
                                        {'name': 0.000},
                                        {'name': 0.000},
                                        {'name': 0.000},
                                        {'name': 0.000},
                                        {'name': 0.000},
                                        {'name': 0.000},
                                        {'name': 0.000},
                                        {'name': 0.000},
                                    ],
                                })

                            else:
                                indicator = []
                                indicator2 = []
                                indicator3 = []
                                indicator4 = []
                                indicator5 = []
                                indicator6 = []
                                indicator7 = []
                                total_month = []
                                if s['campo'] == 'total_cobranza':
                                    carton = self._get_lines_query(
                                        options, df, 'venta_carton')
                                    papel = self._get_lines_query(
                                        options, df, 'venta_papel')
                                    ingresos = self._get_indicators_line(
                                        options, df, 'other_receipts')
                                    indicator.append({'total_cobranza': (carton[0]['venta_carton'] if carton else 0) + (
                                        papel[0]['venta_papel'] if papel else 0) + (ingresos[0]['other_receipts'] if ingresos else 0)})

                                    carton2 = self._get_lines_query(
                                        options, df2, 'venta_carton')
                                    papel2 = self._get_lines_query(
                                        options, df2, 'venta_papel')
                                    ingresos2 = self._get_indicators_line(
                                        options, df2, 'other_receipts')
                                    indicator2.append({'total_cobranza': (carton2[0]['venta_carton'] if carton2 else 0) + (
                                        papel2[0]['venta_papel'] if papel2 else 0) + (ingresos2[0]['other_receipts'] if ingresos2 else 0)})

                                    carton3 = self._get_lines_query(
                                        options, df3, 'venta_carton')
                                    papel3 = self._get_lines_query(
                                        options, df3, 'venta_papel')
                                    ingresos3 = self._get_indicators_line(
                                        options, df3, 'other_receipts')
                                    indicator3.append({'total_cobranza': (carton3[0]['venta_carton'] if carton3 else 0) + (
                                        papel3[0]['venta_papel'] if papel3 else 0) + (ingresos3[0]['other_receipts'] if ingresos3 else 0)})

                                    carton4 = self._get_lines_query(
                                        options, df4, 'venta_carton')
                                    papel4 = self._get_lines_query(
                                        options, df4, 'venta_papel')
                                    ingresos4 = self._get_indicators_line(
                                        options, df4, 'other_receipts')
                                    indicator4.append({'total_cobranza': (carton4[0]['venta_carton'] if carton4 else 0) + (
                                        papel4[0]['venta_papel'] if papel4 else 0) + (ingresos4[0]['other_receipts'] if ingresos4 else 0)})

                                    carton5 = self._get_lines_query(
                                        options, df5, 'venta_carton')
                                    papel5 = self._get_lines_query(
                                        options, df5, 'venta_papel')
                                    ingresos5 = self._get_indicators_line(
                                        options, df5, 'other_receipts')
                                    indicator5.append({'total_cobranza': (carton5[0]['venta_carton'] if carton5 else 0) + (
                                        papel5[0]['venta_papel'] if papel5 else 0) + (ingresos5[0]['other_receipts'] if ingresos5 else 0)})

                                    carton6 = self._get_lines_query(
                                        options, df6, 'venta_carton')
                                    papel6 = self._get_lines_query(
                                        options, df6, 'venta_papel')
                                    ingresos6 = self._get_indicators_line(
                                        options, df6, 'other_receipts')
                                    indicator6.append({'total_cobranza': (carton6[0]['venta_carton'] if carton6 else 0) + (
                                        papel6[0]['venta_papel'] if papel6 else 0) + (ingresos6[0]['other_receipts'] if ingresos6 else 0)})

                                    carton7 = self._get_lines_query(
                                        options, df7, 'venta_carton')
                                    papel7 = self._get_lines_query(
                                        options, df7, 'venta_papel')
                                    ingresos7 = self._get_indicators_line(
                                        options, df7, 'other_receipts')
                                    indicator7.append({'total_cobranza': (carton7[0]['venta_carton'] if carton7 else 0) + (
                                        papel7[0]['venta_papel'] if papel7 else 0) + (ingresos7[0]['other_receipts'] if ingresos7 else 0)})

                                    carton8 = self._get_total_query(
                                        options, new_date_from, df, 'venta_carton')
                                    papel8 = self._get_total_query(
                                        options, new_date_from, df, 'venta_papel')
                                    ingresos8 = self._get_total_indicators(
                                        options, new_date_from, df, 'other_receipts')
                                    total_month.append({'total_cobranza': (carton8[0]['venta_carton'] if carton8 else 0) + (
                                        papel8[0]['venta_papel'] if papel8 else 0) + (ingresos8[0]['other_receipts'] if ingresos8 else 0)})

                                elif s['campo'] == 'total_pagos':
                                    contado = self._get_lines_query(
                                        options, df, 'contado')
                                    cartera = self._get_lines_query(
                                        options, df, 'cartera')
                                    proyecto = self._get_lines_query(
                                        options, df, 'project')
                                    indicator.append({'total_pagos': (contado[0]['contado'] if contado else 0) + (
                                        cartera[0]['cartera'] if cartera else 0) + (proyecto[0]['project'] if proyecto else 0)})

                                    contado2 = self._get_lines_query(
                                        options, df2, 'contado')
                                    cartera2 = self._get_lines_query(
                                        options, df2, 'cartera')
                                    proyecto2 = self._get_lines_query(
                                        options, df2, 'project')
                                    indicator2.append({'total_pagos': (contado2[0]['contado'] if contado2 else 0) + (
                                        cartera2[0]['cartera'] if cartera2 else 0) + (proyecto2[0]['project'] if proyecto2 else 0)})

                                    contado3 = self._get_lines_query(
                                        options, df3, 'contado')
                                    cartera3 = self._get_lines_query(
                                        options, df3, 'cartera')
                                    proyecto3 = self._get_lines_query(
                                        options, df3, 'project')
                                    indicator3.append({'total_pagos': (contado3[0]['contado'] if contado3 else 0) + (
                                        cartera3[0]['cartera'] if cartera3 else 0) + (proyecto3[0]['project'] if proyecto3 else 0)})

                                    contado4 = self._get_lines_query(
                                        options, df4, 'contado')
                                    cartera4 = self._get_lines_query(
                                        options, df4, 'cartera')
                                    proyecto4 = self._get_lines_query(
                                        options, df4, 'project')
                                    indicator4.append({'total_pagos': (contado4[0]['contado'] if contado4 else 0) + (
                                        cartera4[0]['cartera'] if cartera4 else 0) + (proyecto4[0]['project'] if proyecto4 else 0)})

                                    contado5 = self._get_lines_query(
                                        options, df5, 'contado')
                                    cartera5 = self._get_lines_query(
                                        options, df5, 'cartera')
                                    proyecto5 = self._get_lines_query(
                                        options, df5, 'project')
                                    indicator5.append({'total_pagos': (contado5[0]['contado'] if contado5 else 0) + (
                                        cartera5[0]['cartera'] if cartera5 else 0) + (proyecto5[0]['project'] if proyecto5 else 0)})

                                    contado6 = self._get_lines_query(
                                        options, df6, 'contado')
                                    cartera6 = self._get_lines_query(
                                        options, df6, 'cartera')
                                    proyecto6 = self._get_lines_query(
                                        options, df6, 'project')
                                    indicator6.append({'total_pagos': (contado6[0]['contado'] if contado6 else 0) + (
                                        cartera6[0]['cartera'] if cartera6 else 0) + (proyecto6[0]['project'] if proyecto6 else 0)})

                                    contado7 = self._get_lines_query(
                                        options, df7, 'contado')
                                    cartera7 = self._get_lines_query(
                                        options, df7, 'cartera')
                                    proyecto7 = self._get_lines_query(
                                        options, df7, 'project')
                                    indicator7.append({'total_pagos': (contado7[0]['contado'] if contado7 else 0) + (
                                        cartera7[0]['cartera'] if cartera7 else 0) + (proyecto7[0]['project'] if proyecto7 else 0)})

                                    date_initial = datetime.fromisoformat(
                                        new_date_from)
                                    diferencia = df - date_initial.date()
                                    iterator = 0
                                    total = 0
                                    while (iterator < (diferencia.days + 1)):
                                        contado8 = self._get_lines_query(options, fields.Date.from_string(
                                            date_initial.date())+timedelta(days=iterator), str('contado'))
                                        cartera8 = self._get_lines_query(options, fields.Date.from_string(
                                            date_initial.date())+timedelta(days=iterator), str('cartera'))
                                        proyecto8 = self._get_lines_query(options, fields.Date.from_string(
                                            date_initial.date())+timedelta(days=iterator), str('project'))
                                        total = total + (contado8[0]['contado'] if contado8 else 0) + (
                                            cartera8[0]['cartera'] if cartera8 else 0) + (proyecto8[0]['project'] if proyecto8 else 0)
                                        iterator = iterator + 1

                                    total_month.append({'total_pagos': total})

                                else:
                                    indicator = self._get_lines_query(
                                        options, df, str(s['campo']))
                                    indicator2 = self._get_lines_query(
                                        options, df2, str(s['campo']))
                                    indicator3 = self._get_lines_query(
                                        options, df3, str(s['campo']))
                                    indicator4 = self._get_lines_query(
                                        options, df4, str(s['campo']))
                                    indicator5 = self._get_lines_query(
                                        options, df5, str(s['campo']))
                                    indicator6 = self._get_lines_query(
                                        options, df6, str(s['campo']))
                                    indicator7 = self._get_lines_query(
                                        options, df7, str(s['campo']))

                                    if s['campo'] == 'cartera' or s['campo'] == 'contado' or s['campo'] == 'project':
                                        date_initial = datetime.fromisoformat(new_date_from)
                                        diferencia = df - date_initial.date()
                                        iterator = 0
                                        total = 0
                                        while (iterator < (diferencia.days + 1)):
                                            consulta = self._get_lines_query(options, fields.Date.from_string(
                                                date_initial.date())+timedelta(days=iterator), s['campo'])
                                            total = total + \
                                                (consulta[0][s['campo']]
                                                if consulta else 0)
                                            iterator = iterator + 1

                                        total_month.append({s['campo']: total})

                                    else:
                                        total_month = self._get_total_query(
                                            options, new_date_from, df, str(s['campo']))

                                if s['campo'] == 'kg_carton' or s['campo'] == 'kg_papel' or s['campo'] == 'kg_puebla':
                                    promedio = self._get_total_query(
                                        options, df7, df, str(s['campo']))
                                    totalsemana = promedio[0][s['campo']
                                                              ] if promedio or promedio[0][s['campo']] is None else 0
                                elif s['campo'] == 'price_lam':
                                    promedio = self._get_total_indicators(
                                        options, df7, df, str(s['campo']))
                                    totalsemana = promedio[0][s['campo']
                                                              ] if promedio else 0
                                else:
                                    totalsemana = (indicator[0][s['campo']] if indicator else 0) + (indicator2[0][s['campo']] if indicator2 else 0) + (indicator3[0][s['campo']] if indicator3 else 0) + (
                                        indicator4[0][s['campo']] if indicator4 else 0) + (indicator5[0][s['campo']] if indicator5 else 0) + (indicator6[0][s['campo']] if indicator6 else 0) + (indicator7[0][s['campo']] if indicator7 else 0)

                                if totalsemana is None:
                                    totalsemana = 0
                                if total_month[0][s['campo']] is None:
                                    total_month[0][s['campo']] = 0

                                lines.append({
                                    'id': 'fibras',
                                    'name': str(s['subheader']),
                                    'level': 2,
                                    'class': 'concepto',
                                    'columns': [
                                        {'name': "{:,.3f}".format(
                                            indicator7[0][s['campo']]) if indicator7 else "{:,.3f}".format(0)},
                                        {'name': "{:,.3f}".format(
                                            indicator6[0][s['campo']]) if indicator6 else "{:,.3f}".format(0)},
                                        {'name': "{:,.3f}".format(
                                            indicator5[0][s['campo']]) if indicator5 else "{:,.3f}".format(0)},
                                        {'name': "{:,.3f}".format(
                                            indicator4[0][s['campo']]) if indicator4 else "{:,.3f}".format(0)},
                                        {'name': "{:,.3f}".format(
                                            indicator3[0][s['campo']]) if indicator3 else "{:,.3f}".format(0)},
                                        {'name': "{:,.3f}".format(
                                            indicator2[0][s['campo']]) if indicator2 else "{:,.3f}".format(0)},
                                        {'name': "{:,.3f}".format(
                                            indicator[0][s['campo']]) if indicator else "{:,.3f}".format(0)},
                                        {'name': "{:,.3f}".format(
                                            totalsemana)},
                                        {'name': "{:,.3f}".format(
                                            total_month[0][s['campo']]) if total_month else "{:,.3f}".format(0)},
                                    ],
                                })

        return lines

    @api.model
    def _get_report_name(self):
        return _('Reporte de Indicadores')
