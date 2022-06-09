# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

RH_REQUISITION_STATES = [
    ('cancel', 'Rechazado'),
    ('draft', 'Borrador'),
    ('in_progress', 'Confirmado'),
    ('aprovee_ri', 'Aprobado Gerencia RI'),
    ('aprovee_dg', 'Aprobado Direccion General'),
    ('done', 'Cerrado'),
]

class salary_increase(models.Model):
    _name = 'hr.salary.increase'
    _inherit = ['mail.thread']
    _description = "Hr Salary Increase Personal"

    state = fields.Selection(
        RH_REQUISITION_STATES,
        'Estado',
        tracking=True,
        required=True,
        copy=False,
        default='draft'
    )
    name = fields.Char(
        required=True,
        default='Borrador',
        store=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Solicitó',
        default= lambda self: self.env.user,
        copy=False,
        store=True,
    )
    hr_employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Nombre',
        store=True,
    )
    code_employee = fields.Char(
        required=True,
        default='Codigo de colaborador',
        store=True,
    )
    hr_job_current_id= fields.Many2one(
        comodel_name='hr.job',
        string='Puesto Actual',
        copy=False,
        store=True,
    )

    hr_job_proposed_id= fields.Many2one(
        comodel_name='hr.job',
        string='Puesto Propuesto',
        copy=False,
        store=True,
    )

    nivel_current= fields.Integer(
        string='Nivel Actual',
        copy=False,
        store=True,
    )

    nivel_new= fields.Integer(
        string='Nuevo Nivel',
        copy=False,
        store=True,
    )

    daily_salary_current = fields.Float(
        string='Salario Diario Actual',
        copy=False,
        store=True,
    )

    daily_salary_new = fields.Float(
        string='Salario Diario Nuevo',
        copy=False,
        store=True,
    )

    month_salary_current_brut = fields.Float(
        string='Salario Mensual Bruto Actual',
        copy=False,
        store=True,
    )

    month_salary_new_brut = fields.Float(
        string='Salario Mensual Bruto Nuevo',
        copy=False,
        store=True,
    )

    requisition_date = fields.Date(
        required=True,
        string='Fecha de Solicitud',
        tracking=True,
        copy=False,
        default=fields.Date.context_today,
    )

    date_applied = fields.Date(
        required=True,
        string='Fecha de Aplicacion o retroactivo al:',
        tracking=True,
        copy=False,
    )

    justify = fields.Html(
        store=True,
    )
    gratification = fields.Float(
        string='Monto de Gratificacion',
        copy=False,
        store=True,
    )
    justify_gratification = fields.Html(
        store=True,
    )


    def action_in_progress(self):
        self.write({'state': 'in_progress'})


    def action_aprovee_ri(self):
        self.write({'state': 'aprovee_ri'})


    def action_aprovee_dg(self):
        self.write({'state': 'aprovee_dg'})


    def action_cancel(self):
        self.write({'state': 'cancel'})


    def action_done(self):
        self.write({'state': 'done'})


    def action_draft(self):
        self.write({'state': 'draft'})


    def unlink(self):
        for s in self:
            if (s.state!='draft') :
                raise UserError(_('No puedes realizar esta operacion'))
        return super(salary_increase, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.salary.increase') or '/'
        return super(salary_increase, self).create(vals)
