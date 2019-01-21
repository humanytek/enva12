# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models


class Account_invoice_nova(models.Model):
    _inherit = 'account.invoice'

    order_purchase_id = fields.Char(
        string='Purchase Order Customer',
        store=True,
    )

    type_currency = fields.Float(
        # string='Type Currency',
        compute='_get_type_currency',
        digits=(8,6),
        store=True,
        index=True,
    )
    payment_name=fields.Char(
        related='payment_ids.name',
        string='Referencia de Pago',
    )
    payment_amount=fields.Monetary(
        related='payment_ids.amount',
        string='Monto Pagado',
    )
    payment_date=fields.Date(
        related='payment_ids.payment_date',
        string='Fecha de Pago',
    )
    dias_transcurridos=fields.Integer(
        compute='_diferencia',
        string='Dias Transcurridos',
    )

    @api.depends('date_invoice','payment_date')
    def _diferencia(self):
        for r in self:
            if r.payment_date and r.date_invoice:
                r.dias=r.payment_date-r.date_invoice
                r.dias_transcurridos=r.dias.days
            else:
                r.dias_transcurridos=0



    @api.depends('amount_total_company_signed', 'amount_total_signed')
    def _get_type_currency(self):
        for r in self:
            if r.amount_total_company_signed > 0 :
                r.type_currency = r.amount_total_company_signed / r.amount_total_signed

    tax_company = fields.Float(
        compute='_get_tax_company',
        store=True,
    )

    @api.depends('amount_total_company_signed', 'amount_untaxed_signed')
    def _get_tax_company(self):
        for r in self:
            r.tax_company = r.amount_total_company_signed - r.amount_untaxed_signed
