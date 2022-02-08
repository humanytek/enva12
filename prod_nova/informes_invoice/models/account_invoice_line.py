# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Invoice_line(models.Model):
    _inherit= 'account.move.line'

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
        related='account_id.invoice_date',
        store=True,
    )
    number=fields.Char(
        related='account_id.number',
        store=True,
    )
    name_invoice=fields.Char(
        related='account_id.name',
        store=True,
    )
    state=fields.Selection(
        related='account_id.state',
        store=True,
    )
    total_weight=fields.Float(
        compute='_total_weight',
        store=True,
    )
    user_id=fields.Many2one(
        related='account_id.invoice_user_id',
        string='Vendedor',
        store=True,
    )
    type_currency = fields.Monetary(
        related='account_id.type_currency',
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
        related='account_id.re_facturado',
        string='Re-Facturado',
        store=True,
    )

    facturado_to=fields.Boolean(
    related='account_id.facturado_to',
    string='Facturado a:',
    store=True,
    )

    not_accumulate=fields.Boolean(
    related='account_id.not_accumulate',
    string='No Acumular',
    store=True,
    )

    date_applied = fields.Date(
        related='account_id.date_applied',
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
