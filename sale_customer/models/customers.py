# -*- coding: utf-8 -*-
from odoo import api, fields, models

from datetime import datetime, date, time, timedelta

class Customers(models.Model):

    _inherit = 'res.partner'

    payment_conditions = fields.Char(
        compute='_get_conditions',
        string='Condiciones de pago',
    )

    @api.depends('property_payment_term_id')
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

    @api.depends('property_payment_term_id')
    def _get_creditdays(self):
        for d in self:
            if d.property_payment_term_id:
                d.credit_days = d.property_payment_term_id.line_ids.days


    aux = fields.Date(
        compute='_get_aux',
        string='Ultima venta',
    )

    def _get_aux(self):

        for a in self:
            alfa = date(2000, 12, 25)
            lista = a.invoice_ids
            for l in lista:
                if l.date_invoice:
                    if l.date_invoice > alfa:
                        alfa = l.date_invoice
                a.aux = alfa
