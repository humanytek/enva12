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


class ReportsCustomInvCustomer(models.AbstractModel):
    _name = "report.custom.inv.customer"
    _description = "Custom Reports Inventory"
    _inherit = 'account.report'

    filter_date = {'mode': 'single', 'filter': 'today'}
    # filter_all_entries = False


    def _get_columns_name(self, options):
        return [
                {'name': ''},
                {'name': _('TONELADAS'), 'class': 'number', 'style': 'white-space:nowrap; color:#1e3c64; font-size:18px;'},
                {'name': _('%'), 'class': 'number', 'style': 'white-space:nowrap; color:#1e3c64; font-size:18px;'},
        ]


    def _weight_line(self,options,line_id):



        sql_query= """
                        SELECT 
                            partner.name as partner_name,
                            COALESCE(sum(sq.quantity * pp.weight),0) as toneladas
                            from stock_quant sq
                            left join product_product pp on pp.id = sq.product_id
                            left join product_template pt on pt.id = pp.product_tmpl_id
                            left join stock_location sl on sl.id = sq.location_id
                            left join res_partner partner ON partner.id = pt.partner_cus_id
                            where sl.usage = 'internal'
                            and pt.categ_id IN (65,66,67,68,139,147)
                            and pt.sale_ok is true
                            and sl.id not in (39,52,35)
                            and pt.partner_cus_id in (select id from res_partner where stock_whp='True')
                            and sq.quantity > 0
                            GROUP BY partner.name
                            ORDER BY toneladas desc
        """    



        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _weight_line_st(self,options,line_id):



        sql_query= """
                        SELECT 
                            COALESCE(sum(sq.quantity * pp.weight),0) as toneladas
                            from stock_quant sq
                            left join product_product pp on pp.id = sq.product_id
                            left join product_template pt on pt.id = pp.product_tmpl_id
                            left join stock_location sl on sl.id = sq.location_id
                            where sl.usage = 'internal'
                            and pt.categ_id IN (65,66,67,68,139,147)
                            and pt.sale_ok is true
                            and pt.partner_cus_id is null
                            and sl.id not in (39,52,35)
                            and sq.quantity > 0
                           
        """    



        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    def _weight_line_t(self,options,line_id):



        sql_query= """
                        SELECT 
                            COALESCE(sum(sq.quantity * pp.weight),0) as toneladas
                            from stock_quant sq
                            left join product_product pp on pp.id = sq.product_id
                            left join product_template pt on pt.id = pp.product_tmpl_id
                            left join stock_location sl on sl.id = sq.location_id
                            left join res_partner partner ON partner.id = pt.partner_cus_id
                            where sl.usage = 'internal'
                            and pt.categ_id IN (65,66,67,68,139,147)
                            and pt.sale_ok is true
                            and sl.id not in (39,52,35)
                            and sq.quantity > 0
                            
        """    



        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        # if result==None:
        #     result=(0,)

        return result

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        # clientes_stock=self.env['res.partner'].search([('stock_whp','=',True)])
        total_weight=self._weight_line(options,line_id)
        total_weight_t=self._weight_line_t(options,line_id)
        subtotalweight=0
        subtotalwporct=0
        lines.append({
        'id': 'cliente',
        'name': 'CLIENTES CON STOCK',
        'style': 'white-space:nowrap; color:#1e3c64; font-size:21px;',
        'level': 0,
        'class': 'cliente',
        'columns':[
                {'name':''},
                {'name':''},
               
        ],
        })
        if total_weight:
           for tw in total_weight:
                subtotalweight+=tw['toneladas']
                subtotalwporct+=((tw['toneladas'])/1000)/((total_weight_t[0]['toneladas'])/1000)
                lines.append({
                'id': 'cliente',
                'name': str(tw['partner_name']),
                'style': 'white-space:nowrap; font-size:17px;',
                'level': 2,
                'class': 'cliente',
                'columns':[
                    #   {'name':""},
                        {'name':"{:,.3f}".format((tw['toneladas'])/1000) if total_weight else 0 },
                        {'name':"{:.0%}".format(((tw['toneladas'])/1000)/((total_weight_t[0]['toneladas'])/1000)) if total_weight else 0 },
                ],
                })

        lines.append({
                'id': 'total',
                'name': 'SUBTOTAL',
                'style': 'white-space:nowrap; color:#1e3c64; font-size:19px;',
                'level': 0,
                'class': 'total',
                'columns':[
                            {'name':"{:,.3f}".format((subtotalweight)/1000)},
                            {'name':"{:.0%}".format(subtotalwporct)  },
                ],
                })

        lines.append({
        'id': 'cliente',
        'name': 'CLIENTES SIN STOCK',
        'style': 'white-space:nowrap; color:#1e3c64; font-size:21px;',
        'level': 0,
        'class': 'cliente',
        'columns':[
                {'name':''},
                {'name':''},
               
        ],
        })    
        total_weight_st=self._weight_line_st(options,line_id)
        if total_weight_st:
           for tw in total_weight_st:
                
                lines.append({
                'id': 'cliente',
                'name': 'OTROS CLIENTES',
                'style': 'white-space:nowrap;font-size:17px;',
                'level': 2,
                'class': 'cliente',
                'columns':[
                    #   {'name':""},
                        {'name':"{:,.3f}".format((tw['toneladas'])/1000) if total_weight_st else 0 },
                        {'name':"{:.0%}".format(((tw['toneladas'])/1000)/((total_weight_t[0]['toneladas'])/1000)) if total_weight_st else 0 },
                ],
                })
        lines.append({
                    'id': 'total',
                    'name': 'TOTAL',
                    'style': 'white-space:nowrap; color:#1e3c64; font-size:21px;',
                    'level': 0,
                    'class': 'total',
                    'columns':[
                    {'name':"{:,.3f}".format((total_weight_t[0]['toneladas'])/1000) if total_weight_t else 0 },
                    {'name':"{:.0%}".format(((total_weight_t[0]['toneladas'])/1000)/((total_weight_t[0]['toneladas'])/1000)) if total_weight_t else 0 },
                   
                    ],
                    })
        return lines


    @api.model
    def _get_report_name(self):
        return _('Inventario de Clientes con Stock')