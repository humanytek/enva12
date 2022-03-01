# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

MANTTO_REQUISITION_STATES = [
    ('cancel', 'Cancel'),
    ('draft', 'Draft'),
    ('in_progress', 'Confirmed'),
    ('done', 'Closed'),
]
PRIORITY = [
('0','Muy baja'),
('1','Baja'),
('2','Normal'),
('3','Alta'),
]
class Maintenance_requisition(models.Model):
    _name = 'maintenance.requisition'
    _inherit = ['mail.thread']

    name = fields.Char(
        required=True,
        default='New',
        store=True,
    )

    reference=fields.Char(
        required=True,
        string="Referencia",
        store=True,
    )

    date_request = fields.Date(

        string="Fecha de Solicitud",
        store=True,
        track_visibility='onchange',
        default=fields.Date.context_today,
    )

    user_id = fields.Many2one(
    comodel_name='res.users',
    string='Responsible',
    default= lambda self: self.env.user,
    store=True,
    )


    assigned_id = fields.Many2one(
    comodel_name='res.users',
    string='Assigned',
    store=True,
    )

    area_id = fields.Many2one(
    comodel_name = 'maintenance.area',
    string = 'Area',
    store = True,
    )

    state = fields.Selection(
    MANTTO_REQUISITION_STATES,
    'Estado',
    track_visibility='onchange',
    required=True,
    copy=False,
    default='draft'
    )

    priority = fields.Selection(
    PRIORITY,
    'Prioridad',
    copy =False,
    )



    note = fields.Html(
    store=True,
    )

    ot_rm_count=fields.Integer(
    compute='_count_ot',
    string='Work Request count',

    )


    def _count_ot(self):
        results = self.env['maintenance.request'].read_group([('mantto_requisition_id', 'in', self.ids)], ['mantto_requisition_id'], ['mantto_requisition_id'])
        dic = {}
        for x in results: dic[x['mantto_requisition_id'][0]] = x['mantto_requisition_id_count']
        for record in self: record['ot_rm_count'] = dic.get(record.id, 0)


    def action_in_progress(self):
        self.write({'state': 'in_progress'})


    def action_done(self):
        self.write({'state': 'done'})


    def action_cancel(self):
        self.write({'state': 'cancel'})


    def action_draft(self):
        self.write({'state': 'draft'})

    def unlink(self):
        for s in self:
            if (s.state=='done') or (s.state=='open') or (s.state=='in_progress'):
                raise UserError(_('No puedes realizar esta operacion'))
        return super(Maintenance_requisition, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.requitition') or '/'
        return super(Maintenance_requisition, self).create(vals)
