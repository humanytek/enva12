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
    date_invoice=fields.Date(
        related='invoice_id.date_invoice',
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
    type_currency = fields.Float(
        related='invoice_id.type_currency',
        store=True,
    )
    price_subtotal_company=fields.Monetary(
        compute='_subtotal_company',
        store=True,

    )
    price_total_company=fields.Monetary(
        compute='_total_company',
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
