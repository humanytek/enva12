# -*- coding: utf-8 -*-
from odoo import api, fields, models
import datetime

class Customers(models.Model):

    _inherit = 'res.partner'

    payment_conditions = fields.Char(
        compute='_get_conditions',
        string='Condiciones de pago',
    )

    def _get_conditions(self):
        for t in self:
            if t.property_payment_term_id:
                #t.payment_conditions = "datos"
                if t.property_payment_term_id.name == "Pago inmediato":
                    t.payment_conditions = "Contado"
                else:
                    t.payment_conditions = "Credito"

    credit_days = fields.Integer(
        string='Dias credito',
        compute='_get_creditdays',
     )

    def _get_creditdays(self):
        for d in self:
            if d.property_payment_term_id:
                lista_tp = d.property_payment_term_id.line_ids
                for z in lista_tp:
                    d.credit_days = z.days

    aux = fields.Date(
        compute='_get_aux',
        string='Ultima venta'
    )

    @api.one
    # @api.depends('invoice_ids')
    def _get_aux(self):
        alfa = datetime.date(2004,1,21)
        for a in self:
            lista = a.invoice_ids
            for aa in lista:
                if aa.date_invoice:
                    if aa.date_invoice > alfa:
                        alfa = aa.date_invoice
                    a.aux = alfa
