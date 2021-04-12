# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Invoice_line(models.Model):
    _inherit= 'account.invoice.line'

    weight=fields.Float(
        related='product_id.weight',
    )
    default_code=fields.Char(
        related='product_id.default_code',
    )
    standard_price=fields.Float(
        related='product_id.standard_price',
    )
    date_invoice=fields.Date(
        related='invoice_id.date_invoice',
        store=True,
    )
    number=fields.Char(
        related='invoice_id.number',
        store=True,
    )
    name_invoice=fields.Char(
        related='invoice_id.name',
        store=True,
    )
    state=fields.Selection(
        related='invoice_id.state',
        store=True,
    )
    total_weight=fields.Float(
        compute='_total_weight',
        store=True,
    )
    user_id=fields.Many2one(
        related='invoice_id.user_id',
        string='Vendedor',
        store=True,
    )
    type_currency = fields.Monetary(
        related='invoice_id.type_currency',
        store=True,
    )
    price_subtotal_company=fields.Monetary(
        compute='_subtotal_company',
        store=True,

    )
    price_per_kg=fields.Float(
        compute='_price_per_kg',
        string='precio por Kg',
        store=True,
    )
    price_total_company=fields.Monetary(
        compute='_total_company',
        store=True,
    )
    re_facturado=fields.Boolean(
        related='invoice_id.re_facturado',
        string='Re-Facturado',
        store=True,
    )
    date_applied = fields.Date(
        related='invoice_id.date_applied',
        string='Fecha Aplicada',
        store=True,
        )

    @api.depends('weight','quantity')
    def _total_weight(self):
        for r in self:
            r.total_weight=r.quantity*r.weight

    @api.depends('type_currency','price_subtotal')
    def _subtotal_company(self):
        for r in self:
            r.price_subtotal_company=r.price_subtotal*r.type_currency

    @api.depends('type_currency','price_total')
    def _total_company(self):
        for r in self:
            r.price_total_company=r.price_total*r.type_currency

    @api.depends('price_subtotal_company','total_weight')
    def _price_per_kg(self):
        for r in self:
            if r.total_weight!=0:
                if r.price_subtotal_company!=0:
                    r.price_per_kg=r.price_subtotal_company/r.total_weight
                else:
                    r.price_per_kg=0
            else:
                r.price_per_kg=0
