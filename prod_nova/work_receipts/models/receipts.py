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
    _description = "Work Receipts"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
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
        tracking=True,
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
    tracking=True,
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
    comodel_name='account.move',
    relation='account_invoice__id_work_receipts_id_rel',
    column1='account_invoice_id',
    column2='work_receips_id',
    string='Invoices',
    tracking=True,
    store=True,
    domain="['&',('move_type', '=', 'in_invoice'),('invoice_origin','ilike',purchase_name)]",
    )
    order_line_ids=fields.Many2many(
    comodel_name='purchase.order.line',
    string='Order purchase lines',
    store=True,
    domain="[('order_id', '=', purchase_id)]",
    tracking=True,
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


    def action_in_progress(self):
        self.write({'state': 'in_progress','user_confirm': self.env.user.id})



    def action_done(self):
        self.write({'state': 'done','user_validate': self.env.user.id})


    def action_cancel(self):
        self.write({'state': 'cancel'})


    def action_draft(self):
        self.write({'state': 'draft'})


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



    def action_wrq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']

        try:
            template_id = ir_model_data.get_object_reference('work_receipts', 'email_template_edi_work_receipts')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'work.receipts',
            'active_model': 'work.receipts',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })


        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]
                # lang = template._render_template(template.lang, ctx['default_model'], ctx['default_res_id'])

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Request for Quotation')
        else:
            ctx['model_description'] = _('Purchase Order')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


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


    def _count_receipts(self):
        results = self.env['work.receipts'].read_group([('purchase_id', 'in', self.ids)], ['purchase_id'], ['purchase_id'])
        dic = {}
        for x in results: dic[x['purchase_id'][0]] = x['purchase_id_count']
        for record in self: record['purchase_id__work_receipts_count'] = dic.get(record.id, 0)
