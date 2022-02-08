# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('administration','To Validate'),
        ('management','To Management'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')



    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.amount_total < self.env.user.company_id.currency_id._convert(order.company_id.po_triple_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
                if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.user.company_id.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                            order.date_order or fields.Date.today()))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_check()
                else:
                    order.write({'state': 'administration'})
            else:
                order.write({'state': 'management'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True
        super(PurchaseOrder, self).button_confirm()


    def button_check(self):
        self.write({'state': 'to approve'})


class Company(models.Model):
    _inherit = 'res.company'

    po_triple_validation_amount = fields.Monetary(string='Triple validation amount', default=100000,
        help="Minimum amount for which a triple validation is required")
