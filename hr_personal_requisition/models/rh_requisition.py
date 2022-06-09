# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

RH_REQUISITION_STATES = [
    ('cancel', 'Rechazado'),
    ('draft', 'Borrador'),
    ('in_progress', 'Confirmado'),
    ('aprovee_rh', 'Aprobado DH'),
    ('aprovee_ri', 'Aprobado Gerencia RI'),
    ('aprovee_dg', 'Aprobado Direccion General'),
    ('aprovee_jf', 'Aprobado Jefatura'),
    ('select_progress', 'Proceso de Seleccion'),
    ('done', 'Cerrado'),
]
RH_REQUISITION_MOTIVE = [
    ('vacante', 'Vacante'),
    ('nuevo_puesto', 'Nuevo Puesto'),
    ('nueva_plaza', 'Nueva Plaza'),
]

RH_MOTIVE_REPLACE = [
    ('finiquito', 'Finiquito'),
    ('renuncia', 'Renuncia'),
    ('incapacidad', 'Incapacidad'),
    ('otros', 'Otros'),
]

RH_TYPE_PAYROLL = [
    ('semanal', 'Semanal'),
    ('catorcenal', 'Catorcenal'),
]
RH_TYPE_CONTRACT = [
    ('planta', 'Planta'),
    ('temporal', 'Temporal'),
]
RH_WORKING_HOURS = [
    ('MATU','lunes-sábado - 06:00 a. m.- 02:00 p. m.'),
    ('VESP','lunes-sábado - 02:00 p. m.- 10:00 p. m.'),
    ('NOCT','lunes-sábado - 10:00 p. m.- 06:00 a. m.'),
    ('1 turno','lunes-sábado - 06:30 a. m.- 06:30 p. m.'),
    ('2 turno','lunes-sábado - 06:30 p. m.- 06:30 a. m.'),
    ('PRIM','lunes-sábado - 06:00 a. m.- 06:00 p. m.'),
    ('SEGU','lunes-sábado - 06:00 p. m.- 06:00 a. m.'),
    ('PATRI1','lunes-domingo - 07:00 a. m.- 07:00 p. m.'),
    ('PATRI2','lunes-domingo - 07:00 p. m.- 07:00 a. m.'),
    ('MANT1','lunes-sábado - 07:00 a. m.- 03:00 p. m.'),
    ('MANT2','lunes-sábado - 07:00 a. m.- 05:00 p. m.'),
    ('ALM1','lunes-domingo - 08:00 a. m.- 04:00 p. m.'),
    ('ADM1','lunes-viernes - 08:00 a. m.- 05:30 p. m.'),
    ('ADM2','lunes-viernes - 08:30 a. m.- 06:00 p. m.'),
    ('ADM3','lunes-viernes - 09:00 a. m.- 06:30 p. m.'),
    ('ADM4','lunes-viernes - 08:00 a. m.- 05:00 p. m.'),
    ('ADM5','sábado - 08:00 a. m.- 11:00 a. m.'),
    ('VESP 2','lunes-sábado - 02:00 p. m.- 09:30 p. m.'),
    ('NOCT 2','lunes-sábado - 09:30 p. m.- 06:00 a. m.'),
    ('10 AMMT','lunes-sábado - 10:00 a. m.- 06:00 p. m.'),
]

class rh_requisition(models.Model):
    _name = 'hr.requisition.personal'
    _description = "Hr Requisition Personal"
    _inherit = ['mail.thread']
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

    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Departamento',
        copy=False,
        store=True,
    )

    hr_job_id= fields.Many2one(
        comodel_name='hr.job',
        string='Nombre de Puesto',
        copy=False,
        store=True,
    )

    account_analytic_account_id =fields.Many2one(
        comodel_name='account.analytic.account',
        string='Centro de Costo',
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
    motive_requisition = fields.Selection(
        RH_REQUISITION_MOTIVE,
        'Motivo Requisicion',
        tracking=True,
        required=True,
        copy=False,
    )

    state = fields.Selection(
        RH_REQUISITION_STATES,
        'Estado',
        tracking=True,
        required=True,
        copy=False,
        default='draft'
    )

    hr_employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Reemplaza a:',
        store=True,
    )

    motive_replace = fields.Selection(
        RH_MOTIVE_REPLACE,
        'Motivo',
        tracking=True,
        copy=False,
    )

    justify = fields.Html(
        store=True,
    )

    type_payroll =  fields.Selection(
        RH_TYPE_PAYROLL,
        'Tipo de nómina',
        tracking=True,
        copy=False,
    )

    type_contract =  fields.Selection(
        RH_TYPE_CONTRACT,
        'Tipo de contrato',
        tracking=True,
        copy=False,
    )

    duration_incapacity = fields.Char(
        string='Duracion',
        store=True,
    )
    duration_contract = fields.Char(
        string='Duracion',

        store=True,
    )
    others = fields.Char(
        store=True,
    )
    working_hours = fields.Selection(
        RH_WORKING_HOURS,
        'Horario Laboral',
        store=True,
        copy=False,
    )

    salary = fields.Char(
        string='SD',
        store=True,
    )

    workforce_current = fields.Char(
        string='Plantilla Actual',
        store=True,
    )

    workforce_new = fields.Char(
        string='Plantilla Nueva',
        store=True,
    )

    internal_promotion = fields.Boolean(
        string="¿Promocion Interna?",
        store=True,
    )
    authorize_id = fields.Many2one(
        comodel_name='res.users',
        string='Autoriza',
        copy=False,
        store=True,
    )
    internal_nominee = fields.Many2many(
        comodel_name='hr.employee',
        string="Candidatos Internos",
        store=True,
    )


    def action_in_progress(self):
        self.write({'state': 'in_progress'})


    def action_aprovee_rh(self):
        self.write({'state': 'aprovee_rh'})


    def action_aprovee_ri(self):
        self.write({'state': 'aprovee_ri'})


    def action_aprovee_dg(self):
        self.write({'state': 'aprovee_dg'})


    def action_aprovee_jf(self):
        for s in self:
            if (s.authorize_id!= s.env.user):
                raise UserError(_('Usuario no esta autorizado para realizar esta accion'))
            else:
                self.write({'state': 'aprovee_jf'})


    def action_select_progress(self):
        for s in self:
            if (s.motive_requisition=='vacante' and s.internal_promotion==True and s.state!='aprovee_jf') :
                raise UserError(_('No puedes realizar esta operacion falta autorizacion'))
            elif (s.motive_requisition=='nuevo_puesto' and s.internal_promotion==True and s.state!='aprovee_jf') :
                raise UserError(_('No puedes realizar esta operacion falta autorizacion'))
            elif (s.motive_requisition=='nueva_plaza' and s.internal_promotion==True and s.state!='aprovee_jf') :
                raise UserError(_('No puedes realizar esta operacion falta autorizacion'))
            else:
                self.write({'state': 'select_progress'})



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
        return super(rh_requisition, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.requisition.personal') or '/'
        return super(rh_requisition, self).create(vals)

    hr_applicant_id__rh_requisition_count=fields.Integer(
    compute='_count_hr_applicant',
    string='Work receipts count',

    )

    def _count_hr_applicant(self):
        results = self.env['hr.applicant'].read_group([('hr_requisition_personal_id', 'in', self.ids)], ['hr_requisition_personal_id'], ['hr_requisition_personal_id'])
        dic = {}
        for x in results: dic[x['hr_requisition_personal_id'][0]] = x['hr_requisition_personal_id_count']
        for record in self: record['hr_applicant_id__rh_requisition_count'] = dic.get(record.id, 0)

class hr_applicant_nova(models.Model):
    _inherit = 'hr.applicant'

    hr_requisition_personal_id = fields.Many2one(
    'hr.requisition.personal',
    string='Requisicion de Personal',
    copy=False
    )

    @api.onchange('hr_requisition_personal_id')
    def _onchange_hr_requisition_personal_id(self):
        if not self.hr_requisition_personal_id:
            return

        requisition = self.hr_requisition_personal_id

        self.job_id=requisition.hr_job_id
        self.department_id=requisition.department_id
