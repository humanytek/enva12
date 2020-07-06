# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import Warning, UserError
from odoo.tools.float_utils import float_compare


class Account_invoice_nova(models.Model):
    _inherit = 'account.invoice'

    order_purchase_id = fields.Char(
        string='Purchase Order Customer',
        store=True,
    )

    type_currency = fields.Monetary(
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
    transfer_ids=fields.Many2many(
    comodel_name='stock.picking',
    relation='invoice_transfer_rel',
    column1='account_invoice_id',
    column2='stock_picking_id',
    store=True,
    )

    re_facturado=fields.Boolean(
    string='Re-Facturado',
    store=True,
    copy=False
    )

    date_applied = fields.Date(
        string='Fecha Aplicada',
        store=True,
        index=True,
        copy=False)

    @api.depends('origin','sale_id')
    def _get_sale_id(self):
        for r in self:
            if r.origin:
                r.sale_id=r.env['sale.order'].search([('name','=',r.origin)])
            else:
                r.sale_id=False


    sale_id = fields.Many2one(
    comodel_name='sale.order',
    string='Sale order',
    compute='_get_sale_id',
    )

    @api.depends('date_invoice','payment_date')
    def _diferencia(self):
        for r in self:
            if r.payment_date and r.date_invoice:
                r.dias=r.payment_date-r.date_invoice
                r.dias_transcurridos=r.dias.days
            else:
                r.dias_transcurridos=0

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: not inv.partner_id):
            raise UserError(_("The field Vendor is required, please complete it to validate the Vendor Bill."))
        if to_open_invoices.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        if to_open_invoices.filtered(lambda inv: not inv.account_id):
            raise UserError(_('No account was found to create the invoice, be sure you have installed a chart of account.'))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        self.write({'date_applied': fields.Date.context_today(self)})
        return to_open_invoices.invoice_validate()
        super(Account_invoice_nova, self).action_invoice_open()


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
