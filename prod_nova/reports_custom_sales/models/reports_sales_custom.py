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


class ReportsSales(models.AbstractModel):
    _name = "report.sales.custom.nova"
    _description = "Reports Sales"
    _inherit = 'report.sales.nova'

    filter_date = {'mode': 'range', 'filter': 'this_month'}

    def _get_columns_name(self, options):
        return [
        {'name': ''},
        {'name': _('ESTIMADO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('FACTURACION'), 'class': 'number', 'style': 'white-space:nowrap;'},
        ]


    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        df=fields.Date.from_string(date_from)
        first_day_previous_fy = self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'] + relativedelta(years=-1)
        last_day_previous_fy = self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(date_from))['date_from'] + timedelta(days=-1)
        invoices = False
        invoicesarchi = self._partner_trendArchi(options,line_id)
        invoiceslamina = False

        # invoices=self.env['account.invoice'].search([('type','in',['out_invoice']),('state','in',['open','in_payment','paid']),('date_applied','>=',date_from),('date_applied','<=',date_to)],order='partner_id ASC,date_applied')
       

        if invoices:

            lines.append({
                    'id': 'cliente',
                    'name': 'CLIENTE',
                    'level': 0,
                    'class': 'cliente',
                    'columns':[
                            {'name':''},
                            {'name':''},
                        

                    ],
            })
            contadorinv=0

            estimado=0
            presupuesto=0
            facturacion=0
            facturacion_mes_ant=0
            porcentcubrimiento=0
            teorico=0
            tprice_per_kgp=0
            tprice_per_kgf=0
            tavancetons=0
            tdesvton=0
            tdesvpricekg=0
            ttendtonsfm=0
            tpromprevyear=0
            tmesprevyear=0
            tprojectventas=0
            desv_price_per_kg=0
            contadorinv=len(invoices)
            for invoice,value in sorted(invoices.items(), key=lambda x:x[1][1], reverse= True)  :
                budget=self._get_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                budget_budget=self._get_budget_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                project_sale=self._get_project_user_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                comentarios = self.env['project.user.sales'].search(['&','&',('name','=',invoice),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))])
                invoices_line=self._invoice_line_partner(options,line_id,str(invoice))
                invoices_line_ant_month=self._invoice_line_partner_ant_month(options,line_id,str(invoice))
                invoices_line_promedio=self._invoice_line_partner_n(options,line_id,str(invoice), str(first_day_previous_fy),str(last_day_previous_fy))
                invoices_line_lymonth=self._invoice_line_partner_n(options,line_id,str(invoice),str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))
                price_per_kg=self._get_budget_sales_price(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
                if price_per_kg and price_per_kg>0:
                    if invoices_line[1]>0:
                        if invoices_line[2]>0:
                             desv_price_per_kg=((invoices_line[1]/invoices_line[2])-price_per_kg)/price_per_kg
                            # desv_price_per_kg=price_per_kg/(invoices_line[1]/invoices_line[2])-1

                        else:
                            desv_price_per_kg=0
                    else:
                        desv_price_per_kg=0
                else:
                    desv_price_per_kg=0


                if project_sale and project_sale!=0:
                    if budget!=0 and budget!=False:
                        porcentcubrimiento=(project_sale/1000)/(budget/1000)
                    else:
                        porcentcubrimiento=0
                else:
                    if invoices_line[2]!=0 and (self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0) and (bussines_days.bussines_days!=0 or bussines_days!=False) and (budget!=False or budget!=0) :
                        porcentcubrimiento=(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days)/(budget/1000)
                    else:
                        porcentcubrimiento=0


                lines.append({
                        'id': str(value[0]),
                        'name': str(value[0]),
                        'level': 2,
                        'class': 'activo',
                        'columns':[
                            {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line[2]/1000))},

                        ],
                        })

                estimado+=budget/1000
                presupuesto+=budget_budget/1000
                facturacion+=invoices_line[2]/1000
                facturacion_mes_ant+=invoices_line_ant_month[2]/1000
                if price_per_kg!=False:
                    tprice_per_kgp+=price_per_kg/contadorinv
                else:
                    tprice_per_kgp+=0
                if invoices_line[1] !=0 or invoices_line[2]!=0:
                    tprice_per_kgf+=(invoices_line[1]/invoices_line[2])/contadorinv
                else:
                    tprice_per_kgf+=0
                tpromprevyear+=(invoices_line_promedio[2]/12)/1000
                tmesprevyear+=invoices_line_lymonth[2]/1000
                if project_sale:
                    tprojectventas+=project_sale/1000
                else:
                    if self._billed_days(options,line_id)!=0:
                        tprojectventas+=((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days
                    else:
                        tprojectventas+=0

            if estimado!=0:
                tavancetons=facturacion/estimado
            else:
                tavancetons=0

            if bussines_days.bussines_days!=0:
                if (estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)!=0:
                    tdesvton=(facturacion/((estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)))-1
                else:
                    tdesvton=0

            else:
                tdesvton=0

            if tprice_per_kgp!=0:
                tdesvpricekg=(tprice_per_kgf-tprice_per_kgp)/tprice_per_kgp
            else:
                tdesvpricekg=0
            if self._billed_days(options,line_id)!=0:
                ttendtonsfm=(facturacion/self._billed_days(options,line_id))*bussines_days.bussines_days
            else:
                ttendtonsfm=0
            if estimado!=0 or bussines_days.bussines_days!=0 or self._billed_days(options,line_id)!=0:
                teorico=(estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)
            else:
                teorico=0





            lines.append({
                    'id': 'total',
                    'name': 'TOTAL',
                    'level': 0,
                    'class': 'total',
                    'columns':[
                    {'name': "{:,}".format(round(estimado))},
                    {'name': "{:,}".format(round(facturacion))},
                    
                    ],
                    })

        if invoicesarchi:
            contadorinv=0

            estimado=0
            presupuesto=0
            facturacion=0
            facturacion_mes_ant=0
            porcentcubrimiento=0
            teorico=0
            tprice_per_kgp=0
            tprice_per_kgf=0
            tavancetons=0
            tdesvton=0
            tdesvpricekg=0
            ttendtonsfm=0
            tpromprevyear=0
            tmesprevyear=0
            tprojectventas=0
            desv_price_per_kg=0
            contadorinv=len(invoicesarchi)
            lines.append({
            'id': 'cliente',
            'name': 'CLIENTE',
            'level': 0,
            'class': 'cliente',
            'columns':[
                    {'name':''},
                    {'name':''},
                    

            ],
            })

            for invoice,value in sorted(invoicesarchi.items(), key=lambda x:x[1][1], reverse= True) :
                budget=self._get_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                budget_budget=self._get_budget_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                project_sale=self._get_project_user_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                comentarios = self.env['project.user.sales'].search(['&','&',('name','=',invoice),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))])
                invoices_line=self._invoice_line_partner(options,line_id,str(invoice))
                invoices_line_ant_month=self._invoice_line_partner_ant_month(options,line_id,str(invoice))
                invoices_line_promedio=self._invoice_line_partner_n(options,line_id,str(invoice), str(first_day_previous_fy),str(last_day_previous_fy))
                invoices_line_lymonth=self._invoice_line_partner_n(options,line_id,str(invoice),str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))
                price_per_kg=self._get_budget_sales_price(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
                if price_per_kg and price_per_kg>0:
                    if invoices_line[1]>0:
                        if invoices_line[2]>0:
                             desv_price_per_kg=((invoices_line[1]/invoices_line[2])-price_per_kg)/price_per_kg
                            # desv_price_per_kg=price_per_kg/(invoices_line[1]/invoices_line[2])-1

                        else:
                            desv_price_per_kg=0
                    else:
                        desv_price_per_kg=0
                else:
                    desv_price_per_kg=0

                if project_sale and project_sale!=0:
                    if budget!=0 and budget!=False:
                        porcentcubrimiento=(project_sale/1000)/(budget/1000)
                    else:
                        porcentcubrimiento=0
                else:
                    if invoices_line[2]!=0 and (self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0) and (bussines_days.bussines_days!=0 or bussines_days!=False) and (budget!=False or budget!=0) :
                        porcentcubrimiento=(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days)/(budget/1000)
                    else:
                        porcentcubrimiento=0

                lines.append({
                        'id': str(value[0]),
                        'name': str(value[0]),
                        'level': 2,
                        'class': 'activo',
                        'columns':[
                            {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line[2]/1000))},
                           

                        ],
                        })

                estimado+=budget/1000
                presupuesto+=budget_budget/1000
                facturacion+=invoices_line[2]/1000
                facturacion_mes_ant+=invoices_line_ant_month[2]/1000
                if price_per_kg!=False:
                    tprice_per_kgp+=price_per_kg/contadorinv
                else:
                    tprice_per_kgp+=0
                if invoices_line[2]!=0 or invoices_line[1]!=0:
                    tprice_per_kgf+=(invoices_line[1]/invoices_line[2])/contadorinv
                else:
                    tprice_per_kgf+=0
                tpromprevyear+=(invoices_line_promedio[2]/12)/1000
                tmesprevyear+=invoices_line_lymonth[2]/1000
                if project_sale:
                    tprojectventas+=project_sale/1000
                else:
                    if self._billed_days(options,line_id)!=0:
                        tprojectventas+=((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days
                    else:
                        tprojectventas+=0

            if estimado!=0:
                tavancetons=facturacion/estimado
            else:
                tavancetons=0

            if bussines_days.bussines_days!=0:
                if (estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)!=0:
                    tdesvton=(facturacion/((estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)))-1
                else:
                    tdesvton=0

            else:
                tdesvton=0

            if tprice_per_kgp!=0:
                tdesvpricekg=(tprice_per_kgf-tprice_per_kgp)/tprice_per_kgp
            else:
                tdesvpricekg=0
            if self._billed_days(options,line_id)!=0:
                ttendtonsfm=(facturacion/self._billed_days(options,line_id))*bussines_days.bussines_days
            else:
                ttendtonsfm=0
            if estimado!=0 or bussines_days.bussines_days!=0 or self._billed_days(options,line_id)!=0:
                teorico=(estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)
            else:
                teorico=0



            lines.append({
                    'id': 'total',
                    'name': 'TOTAL',
                    'level': 0,
                    'class': 'total',
                    'columns':[
                    {'name': "{:,}".format(round(estimado))},
                    {'name': "{:,}".format(round(facturacion))},
                   
                    ],
                    })
        if invoiceslamina:
            contadorinv=0

            estimado=0
            presupuesto=0
            facturacion=0
            facturacion_mes_ant=0
            porcentcubrimiento=0
            teorico=0
            tprice_per_kgp=0
            tprice_per_kgf=0
            tavancetons=0
            tdesvton=0
            tdesvpricekg=0
            ttendtonsfm=0
            tpromprevyear=0
            tmesprevyear=0
            tprojectventas=0
            desv_price_per_kg=0
            contadorinv=len(invoiceslamina)
            lines.append({
            'id': 'cliente',
            'name': 'CLIENTE',
            'level': 0,
            'class': 'cliente',
            'columns':[
                    {'name':''},
                    {'name':''},
                   

            ],
            })

            for invoice,value in sorted(invoiceslamina.items(), key=lambda x:x[1][1], reverse= True) :
                budget=self._get_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                budget_budget=self._get_budget_budget_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                project_sale=self._get_project_user_sales(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                comentarios = self.env['project.user.sales'].search(['&','&',('name','=',invoice),('date_from','>=',fields.Date.from_string(date_from)),('date_to','<=',fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))])
                invoices_line=self._invoice_line_partner(options,line_id,str(invoice))
                invoices_line_ant_month=self._invoice_line_partner_ant_month(options,line_id,str(invoice))
                invoices_line_promedio=self._invoice_line_partner_n(options,line_id,str(invoice), str(first_day_previous_fy),str(last_day_previous_fy))
                invoices_line_lymonth=self._invoice_line_partner_n(options,line_id,str(invoice),str(fields.Date.from_string(date_from)+relativedelta(years=-1)),str(fields.Date.from_string(date_from)+relativedelta(months=1,years=-1)+timedelta(days=-1)))
                price_per_kg=self._get_budget_sales_price(invoice, fields.Date.from_string(date_from),fields.Date.from_string(date_from)+relativedelta(months=1)+timedelta(days=-1))
                bussines_days=self.env['bussines.days'].search([('name','=',str(df.month)),('year','=',str(df.year))])
                if price_per_kg and price_per_kg>0:
                    if invoices_line[1]>0:
                        if invoices_line[2]>0:
                             desv_price_per_kg=((invoices_line[1]/invoices_line[2])-price_per_kg)/price_per_kg
                            # desv_price_per_kg=price_per_kg/(invoices_line[1]/invoices_line[2])-1

                        else:
                            desv_price_per_kg=0
                    else:
                        desv_price_per_kg=0
                else:
                    desv_price_per_kg=0

                if project_sale and project_sale!=0:
                    if budget!=0 and budget!=False:
                        porcentcubrimiento=(project_sale/1000)/(budget/1000)
                    else:
                        porcentcubrimiento=0
                else:
                    if invoices_line[2]!=0 and (self._billed_days(options,line_id)!=False or self._billed_days(options,line_id)!=0) and (bussines_days.bussines_days!=0 or bussines_days!=False) and (budget!=False or budget!=0) :
                        porcentcubrimiento=(((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days)/(budget/1000)
                    else:
                        porcentcubrimiento=0

                lines.append({
                        'id': str(value[0]),
                        'name': str(value[0]),
                        'level': 2,
                        'class': 'activo',
                        'columns':[
                            {'name':0 if budget==False else "{:,}".format(round(budget/1000)) },
                            {'name':"{:,}".format(round(invoices_line[2]/1000))},
                           

                        ],
                        })

                estimado+=budget/1000
                presupuesto+=budget_budget/1000
                facturacion+=invoices_line[2]/1000
                facturacion_mes_ant+=invoices_line_ant_month[2]/1000
                if price_per_kg!=False:
                    tprice_per_kgp+=price_per_kg/contadorinv
                else:
                    tprice_per_kgp+=0
                if invoices_line[2]!=0 or invoices_line[1]!=0:
                    tprice_per_kgf+=(invoices_line[1]/invoices_line[2])/contadorinv
                else:
                    tprice_per_kgf+=0
                tpromprevyear+=(invoices_line_promedio[2]/12)/1000
                tmesprevyear+=invoices_line_lymonth[2]/1000
                if project_sale:
                    tprojectventas+=project_sale/1000
                else:
                    if self._billed_days(options,line_id)!=0:
                        tprojectventas+=((invoices_line[2]/1000)/(self._billed_days(options,line_id)))*bussines_days.bussines_days
                    else:
                        tprojectventas+=0

            if estimado!=0:
                tavancetons=facturacion/estimado
            else:
                tavancetons=0

            if bussines_days.bussines_days!=0:
                if (estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)!=0:
                    tdesvton=(facturacion/((estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)))-1
                else:
                    tdesvton=0

            else:
                tdesvton=0

            if tprice_per_kgp!=0:
                tdesvpricekg=(tprice_per_kgf-tprice_per_kgp)/tprice_per_kgp
            else:
                tdesvpricekg=0
            if self._billed_days(options,line_id)!=0:
                ttendtonsfm=(facturacion/self._billed_days(options,line_id))*bussines_days.bussines_days
            else:
                ttendtonsfm=0
            if estimado!=0 or bussines_days.bussines_days!=0 or self._billed_days(options,line_id)!=0:
                teorico=(estimado/bussines_days.bussines_days)*self._billed_days(options,line_id)
            else:
                teorico=0



            lines.append({
                    'id': 'total',
                    'name': 'TOTAL',
                    'level': 0,
                    'class': 'total',
                    'columns':[
                    {'name': "{:,}".format(round(estimado))},
                    {'name': "{:,}".format(round(facturacion))},
                    
                    ],
                    })


        return lines

    @api.model
    def _get_report_name(self):
        return _('Tendencia de Ventas')