# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api

class report_client_payment_nva(models.Model):
    _inherit= 'account.payment'

    tipocambio = fields.Float(
        digits=(7,6),
        string='TipoCambio',
        compute='_tipo_cambio',
        store=True,
    )

    @api.depends('l10n_mx_edi_payment_method_id', 'currency_id', 'date')
    def _tipo_cambio(self):
        hoy = datetime.now()
        f3 = hoy.strftime("%x")
        for cp in self:
            f1 = cp.date.strftime("%x")
            moneda = cp.currency_id.rate_ids
            if f1 == f3:
                fs = f1
            else:
                fs = f1
            for x in moneda:
                f2 = x.name.strftime("%x")
                if fs == f2:
                    cp.tipocambio = 1 / x.rate
