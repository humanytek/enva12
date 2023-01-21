# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountPartnerInvoice(models.Model):
    _inherit = 'account.move'

    dias_vencidos=fields.Integer(
        compute='_diferencia',
        string='Dias Vencidos',
    )

    user_autoriza= fields.Many2one(
        comodel_name='res.users',
        string='Autorizo',
        store=True,
    )
    fecha_aprobacion = fields.Datetime(
        string='Fecha Aprobacion Pago',
        readonly=1,
        index=True,
        copy=False,
        store=True,
    )
    comentarios_pago= fields.Text(
        string='Comentario Pago',
        store=True,
    )

    currency_account=fields.Many2one(
        related='partner_bank_id.currency_id',
        string='Moneda Cuenta',
        readonly=True,
    )

    state_payment = fields.Selection([
            ('no_autorizado','Sin Autorizar'),
            ('autorizado', 'Autorizado'),
        ], string='Estado de pago', index=True, readonly=True, default='no_autorizado',
        tracking=True, copy=False,store=True)



    def _diferencia(self):
        for r in self:
            today=fields.Date.context_today(self)
            if r.invoice_date_due and today:
                dias = today-r.invoice_date_due
                r.dias_vencidos = dias.days
            else:
                r.dias_vencidos = 0



    def action_autorizar_pago(self):
        self.write({'state_payment': 'autorizado','user_autoriza': self.env.user.id,'fecha_aprobacion':fields.datetime.now()})


    def action_des_autorizar_pago(self):
        self.write({'state_payment': 'no_autorizado','user_autoriza': self.env.user.id})
