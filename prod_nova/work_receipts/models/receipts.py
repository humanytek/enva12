# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

WORK_RECEIPS_STATES = [
    ('cancel', 'Cancel'),
    ('draft', 'Draft'),
    ('in_progress', 'Confirmed'),
    ('done', 'Closed'),
]

class Receipts(models.Model):
    _name = 'work.receipts'
    _inherit = ['mail.thread']
    name = fields.Char(
        required=True,
        default='New',
        store=True,
    )

    description = fields.Char(
        required=True,
        string='Description',
    )
    user_confirm= fields.Many2one(
        comodel_name='res.users',
        string='User Confirm',
        store=True,
    )
    user_validate= fields.Many2one(
        comodel_name='res.users',
        string='User Validate',
        store=True,
    )
    receipts_date= fields.Date(
        required=True,
        string='Reception Date',
        track_visibility='onchange',
        default=fields.Date.context_today,
    )
    user_id = fields.Many2one(
    comodel_name='res.users',
    string='Responsible',
    default= lambda self: self.env.user,
    store=True,
    )
    state = fields.Selection(
    WORK_RECEIPS_STATES,
    'Estado',
    track_visibility='onchange',
    required=True,
    copy=False,
    default='draft'
    )
    purchase_id= fields.Many2one(
    comodel_name='purchase.order',
    string='Order Purchase',
    store=True,
    )
    vendor_id=fields.Many2one(
    related='purchase_id.partner_id',
    string='Vendor',
    store=True,
    )
    purchase_name=fields.Char(
    related='purchase_id.name',
    string='Purchase Name',
    store=True,
    )
    invoice_ids=fields.Many2many(
    comodel_name='account.invoice',
    relation='account_invoice__id_work_receipts_id_rel',
    column1='account_invoice_id',
    column2='work_receips_id',
    string='Invoices',
    track_visibility='onchange',
    store=True,
    domain="['&',('type', '=', 'in_invoice'),('origin','ilike',purchase_name)]",
    )
    order_line_ids=fields.Many2many(
    comodel_name='purchase.order.line',
    string='Order purchase lines',
    store=True,
    domain="[('order_id', '=', purchase_id)]",
    track_visibility='onchange',
    )
    advance = fields.Boolean(
    string='Advance',
    store=True,
    )
    progress=fields.Integer(
    string='Progress Work',
    store=True,
    )
    porcent=fields.Integer(
    compute='_porcent',
    string='Porcent',
    store=True,
    )
    observation=fields.Text(
    string='Observation',
    store=True,
    )
    file_doc=fields.Binary(
    string='File',
    store=True,
    )
    amount = fields.Float(
    string='Amount',
    store=True,
    )



    @api.depends('progress','porcent')
    def _porcent(self):
        for p in self:
            p.porcent=p.progress

    @api.multi
    def action_in_progress(self):
        self.write({'state': 'in_progress','user_confirm': self.env.user.id})


    @api.multi
    def action_done(self):
        self.write({'state': 'done','user_validate': self.env.user.id})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        for s in self:
            if (s.state=='done') or (s.state=='open') or (s.state=='in_progress'):
                raise UserError(_('No puedes realizar esta operacion'))
        return super(Receipts, self).unlink()


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('work.receipts') or '/'
        return super(Receipts, self).create(vals)

class Account_invoice_nova(models.Model):
    _inherit = 'purchase.order'

    purchase_id__work_receipts_count=fields.Integer(
    compute='_count_receipts',
    string='Work receipts count',

    )
    service = fields.Boolean(
    string='Service',
    store=True,
    )
    @api.one
    def _count_receipts(self):
        results = self.env['work.receipts'].read_group([('purchase_id', 'in', self.ids)], 'purchase_id', 'purchase_id')
        dic = {}
        for x in results: dic[x['purchase_id'][0]] = x['purchase_id_count']
        for record in self: record['purchase_id__work_receipts_count'] = dic.get(record.id, 0)
