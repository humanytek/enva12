# coding: utf-8

from odoo import api, fields, models, _

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    approver = fields.Many2one(
        'res.users',
        'Approver',
        readonly=True
    )
    date_approve = fields.Datetime(
        'Approval Date',
        readonly=1,
        index=True,
        copy=False
    )
    petitioner = fields.Many2one(
        'res.users',
        'Petitioner',
        related='requisition_id.user_id',
        readonly=True
    )
    petition_date = fields.Datetime(
        'Petition Date',
        related='requisition_id.create_date',
        readonly=True
    )
    validator = fields.Many2one(
        string='Authorized',
        related='requisition_id.validator',
        readonly=True
    )
    date_validator = fields.Datetime(
        string='Authorized Date',
        related='requisition_id.date_validator',
        readonly=1,
        index=True,
        copy=False
    )



    def button_approve(self, force=False):
        res = super (PurchaseOrder, self).button_approve(force = force)
        self.write({'approver':self.env.user.id,'date_approve':fields.datetime.now()})
        return res



class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    validator = fields.Many2one(
        'res.users', 'Approver',
        readonly=True
    )
    date_validator = fields.Datetime(
        'Approval Date',
         readonly=1,
         index=True,
         copy=False
     )



    def action_open(self):
        self.write({'state': 'open','validator':self.env.user.id,'date_validator':fields.datetime.now()})
        super(PurchaseRequisition, self).action_open()
