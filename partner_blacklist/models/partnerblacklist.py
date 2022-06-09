# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import Warning, UserError
from odoo.tools.float_utils import float_compare
from odoo.tools import pycompat

STATES = [
    ('Sentencia Favorable', 'Sentencia Favorable'),
    ('Desvirtuado', 'Desvirtuado'),
    ('Definitivo', 'Definitivo'),
    ('Presunto', 'Presunto'),
]

class ResPartner(models.Model):
    _inherit = 'res.partner'

    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',required=True)

    state_list_sat = fields.Selection(
    [('Confiable', 'Confiable'),
    ('Sentencia Favorable', 'Sentencia Favorable'),
    ('Desvirtuado', 'Desvirtuado'),
    ('Definitivo', 'Definitivo'),
    ('Presunto', 'Presunto'),
    ],string='Estatus Lista 69B',default='Confiable',store=True)


    @api.model_create_multi
    def create(self, vals_list):
        partners = super(ResPartner, self).create(vals_list)
        partner_obj = self.env['partner.blacklist']
        if len(vals_list) == 1:
            exist_supplier = partner_obj.search([('vat', '=', vals_list[0].get('vat', False))], limit=1)
            if (vals_list[0].get('customer', False)==True):
                partners.message_post(
                body=('La empresa con RFC <b>%s</b> de Nombre <b>%s</b> Se encuentra en la Lista del 69B con estatus <b>%s</b> y fue creado por el Usuario : <b>%s</b> Fecha Publicacion: <b>%s</b>'%(vals_list[0].get('vat', False),vals_list[0].get('name', False),exist_supplier.situacion_contribuyente,self.env.user.name,exist_supplier.publi_date)),
                message_type ='email',
                partner_ids = [753,2189,758])
            else:
                if exist_supplier and (exist_supplier.situacion_contribuyente=="Definitivo" or exist_supplier.situacion_contribuyente=="Presunto"):
                    raise UserError(_("Esta Empresa se encuentra en la lista del 69-B con estatus %s no puede continuar con el proceso") % exist_supplier.situacion_contribuyente)
                if exist_supplier and (exist_supplier.situacion_contribuyente=="Desvirtuado" or exist_supplier.situacion_contribuyente=="Sentencia Favorable"):
                    partners.message_post(
                    body=('La empresa con RFC <b>%s</b> de Nombre <b>%s</b> Se encuentra en la Lista del 69B con estatus <b>%s</b> y fue creado por el Usuario : <b>%s</b> Fecha Publicacion: <b>%s</b>'%(vals_list[0].get('vat', False),vals_list[0].get('name', False),exist_supplier.situacion_contribuyente,self.env.user.name,exist_supplier.publi_date)),
                    message_type ='email',
                    partner_ids = [753,2189,758])

        return partners


class PartnerBlacklist(models.Model):
    _name = 'partner.blacklist'

    name = fields.Char(
        required=True,
        string='Nombre del Contribuyente',
        store=True,
    )

    vat = fields.Char(
        required=True,
        store=True,
    )

    publi_date= fields.Date(
        required=True,
        string='Fecha Publicacion',
        store=True,
    )

    situacion_contribuyente =  fields.Selection(
        STATES,
        string='Situación del contribuyente',
        required=True,
        store=True,
    )

    oficio_global_a = fields.Char(
        string='Núm y f. de oficio global de presunción',
        store=True,
    )
    presunto_sat_date= fields.Date(
        string='Publicacion SAT presunto',
        store=True,
    )

    oficio_global_b = fields.Char(
        string='Núm y f. de oficio global de presunción',
        store=True,
    )

    presunto_dof_date= fields.Date(
        string='Publicacion DOF presunto',
        store=True,
    )

    desvirtuado_sat_date= fields.Date(
        string='Publicacion SAT Desvirtuado',
        store=True,
    )

    oficio_global_desvirtuado = fields.Char(
        string='Núm y f. de oficio global de contribuyentes que desvirtuaron',
        store=True,
    )

    desvirtuado_dof_date= fields.Date(
        string='Publicacion DOF Desvirtuado',
        store=True,
    )

    oficio_global_definitivo = fields.Char(
        string='Núm y f. de oficio global definitivos',
        store=True,
    )

    definitivo_sat_date= fields.Date(
        string='Publicacion SAT Definitivo',
        store=True,
    )

    definitivo_dof_date= fields.Date(
        string='Publicacion DOF Definitivo',
        store=True,
    )

    oficio_global_favorable_a = fields.Char(
        string='Núm y f. de oficio global sentencia favorable',
        store=True,
    )

    favorable_sat_date= fields.Date(
        string='Publicacion SAT Sentencia favorable',
        store=True,
    )

    oficio_global_favorable_b = fields.Char(
        string='Núm y f. de oficio global sentencia favorable',
        store=True,
    )

    favorable_dof_date= fields.Date(
        string='Publicacion DOF Sentencia favorable',
        store=True,
    )

    @api.model
    def _update_state_list_sat(self):
        partner = self.env['res.partner'].search([])
        partner_obj = self.env['partner.blacklist']

        for rec in partner:
            exist_supplier = partner_obj.search([('vat', '=',rec.vat)], limit=1)
            if exist_supplier:
                rec.write({'state_list_sat':exist_supplier.situacion_contribuyente})


class Account_invoice_nova(models.Model):
    _inherit = 'account.move'

    state_list_sat=fields.Selection(
    related='partner_id.state_list_sat',
    string='Estatus Lista 69-B',
    store=True,
    )



    def action_autorizar_pago(self):

        to_draft_invoices = self.filtered(lambda inv: inv.state != 'draft')
        if to_draft_invoices.filtered(lambda inv: inv.state_payment !='no_autorizado'):
            raise UserError(_("No puede autorizar nuevamente una factura autorizada."))
        to_draft_invoices.check_autorizar_pago()
        to_draft_invoices.write({'state_payment': 'autorizado','user_autoriza': self.env.user.id,'fecha_aprobacion':fields.datetime.now()})
        super(Account_invoice_nova, self).action_autorizar_pago()


    def check_autorizar_pago(self):
        partner_obj = self.env['partner.blacklist']
        for r in self:
            exist_supplier = partner_obj.search(
                [('vat', '=', r.partner_id.vat)], limit=1)
            if exist_supplier and (exist_supplier.situacion_contribuyente=="Definitivo" or exist_supplier.situacion_contribuyente=="Presunto"):
                raise UserError(_("Esta Empresa se encuentra en la lista del 69-B con estatus %s no puede continuar con el proceso") % exist_supplier.situacion_contribuyente)
        return



    def action_autorizar_list_pago(self):
        partner_obj = self.env['partner.blacklist']
        exist_supplier = partner_obj.search(
            [('vat', '=', self.partner_id.vat)], limit=1)

        self.write({'state_payment': 'autorizado','user_autoriza': self.env.user.id,'fecha_aprobacion':fields.datetime.now()})
        self.message_post(body=('La empresa con RFC <b>%s</b> de Nombre <b>%s</b> Se encuentra en la Lista del 69B con estatus <b>%s</b> y fue autorizado por el Usuario : <b>%s</b> Fecha Publicacion: <b>%s</b>'%(self.partner_id.vat,self.partner_id.name,exist_supplier.situacion_contribuyente,self.env.user.name,exist_supplier.publi_date)),message_type ='email',partner_ids = [753,2189,758,self.env.user])


    def action_invoice_open(self):

        partner_obj = self.env['partner.blacklist']
        exist_supplier = partner_obj.search(
            [('vat', '=', self.partner_id.vat)], limit=1)
        if exist_supplier and (exist_supplier.situacion_contribuyente=="Definitivo" or exist_supplier.situacion_contribuyente=="Presunto"):
            raise UserError(_("Esta Empresa se encuentra en la lista del 69-B con estatus %s no puede continuar con el proceso") % exist_supplier.situacion_contribuyente)
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: not inv.partner_id):
            raise UserError(_("The field Vendor is required, please complete it to validate the Vendor Bill."))
        if to_open_invoices.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        if to_open_invoices.filtered(lambda inv: not inv.account_id):
            raise UserError(_('No account was found to create the invoice, be sure you have installed a chart of account.'))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        self.write({'date_applied': fields.Date.context_today(self)})
        return to_open_invoices.invoice_validate()
        super(Account_invoice_nova, self).action_invoice_open()


    def action_invoice_list_open(self):

        partner_obj = self.env['partner.blacklist']
        exist_supplier = partner_obj.search(
            [('vat', '=', self.partner_id.vat)], limit=1)
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: not inv.partner_id):
            raise UserError(_("The field Vendor is required, please complete it to validate the Vendor Bill."))
        if to_open_invoices.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        if to_open_invoices.filtered(lambda inv: not inv.account_id):
            raise UserError(_('No account was found to create the invoice, be sure you have installed a chart of account.'))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        self.write({'date_applied': fields.Date.context_today(self)})
        self.message_post(body=('La empresa con RFC <b>%s</b> de Nombre <b>%s</b> Se encuentra en la Lista del 69B con estatus <b>%s</b> y fue autorizado por el Usuario : <b>%s</b> Fecha Publicacion: <b>%s</b>'%(self.partner_id.vat,self.partner_id.name,exist_supplier.situacion_contribuyente,self.env.user.name,exist_supplier.publi_date)),message_type ='email',partner_ids = [753,2189,758,self.env.user])
        return to_open_invoices.invoice_validate()

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        bank_id = False
        warning = {}
        domain = {}

        partner_obj = self.env['partner.blacklist']
        exist_supplier = partner_obj.search(
            [('vat', '=', self.partner_id.vat)], limit=1)
        if exist_supplier:
            warning = {
                'title': _('Esta Empresa se encuentra en la lista del 69-B con el estatus %s!'%exist_supplier.situacion_contribuyente),
                'message' : _('Favor de contactar al departamento de contabilidad para seguir el proceso'),
            }
            return {'warning': warning}

        company_id = self.company_id.id
        p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
        type = self.type or self.env.context.get('type', 'out_invoice')
        if p:
            rec_account = p.property_account_receivable_id
            pay_account = p.property_account_payable_id
            if not rec_account and not pay_account:
                action = self.env.ref('account.action_account_config')
                msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('in_invoice', 'in_refund'):
                account_id = pay_account.id
                payment_term_id = p.property_supplier_payment_term_id.id
            else:
                account_id = rec_account.id
                payment_term_id = p.property_payment_term_id.id

            delivery_partner_id = self.get_delivery_partner_id()
            fiscal_position = p.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, delivery_id=delivery_partner_id)

            # If partner has no warning, check its company
            if p.invoice_warn == 'no-message' and p.parent_id:
                p = p.parent_id
            if p.invoice_warn and p.invoice_warn != 'no-message':
                # Block if partner only has warning but parent company is blocked
                if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
                    p = p.parent_id
                warning = {
                    'title': _("Warning for %s") % p.name,
                    'message': p.invoice_warn_msg
                    }
                if p.invoice_warn == 'block':
                    self.partner_id = False

        self.account_id = account_id
        if payment_term_id:
            self.payment_term_id = payment_term_id
        self.date_due = False
        self.fiscal_position_id = fiscal_position

        if type in ('in_invoice', 'out_refund'):
            bank_ids = p.commercial_partner_id.bank_ids
            bank_id = bank_ids[0].id if bank_ids else False
            self.partner_bank_id = bank_id
            domain = {'partner_bank_id': [('id', 'in', bank_ids.ids)]}
        elif type == 'out_invoice':
            domain = {'partner_bank_id': [('partner_id.ref_company_ids', 'in', [self.company_id.id])]}

        res = {}
        if warning:
            res['warning'] = warning
        if domain:
            res['domain'] = domain
        return res
        super(Account_invoice_nova, self)._onchange_partner_id()


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    def button_confirm(self):
        partner_obj = self.env['partner.blacklist']
        partner = self.partner_id
        exist_supplier = partner_obj.search(
            [('vat', '=', partner.vat )], limit=1)
        if exist_supplier and (exist_supplier.situacion_contribuyente=="Definitivo" or exist_supplier.situacion_contribuyente=="Presunto"):
            raise UserError(_("Esta Empresa se encuentra en la lista del 69-B con estatus %s no puede continuar con el proceso") % exist_supplier.situacion_contribuyente)
        if exist_supplier and (exist_supplier.situacion_contribuyente=="Desvirtuado" or exist_supplier.situacion_contribuyente=="Sentencia Favorable"):
            self.message_post(body=('La empresa con RFC <b>%s</b> de Nombre <b>%s</b> Se encuentra en la Lista del 69B con estatus <b>%s</b> y fue autorizado por el Usuario : <b>%s</b> Fecha Publicacion: <b>%s</b>'%(self.partner_id.vat,self.partner_id.name,exist_supplier.situacion_contribuyente,self.env.user.name,exist_supplier.publi_date)),message_type ='email',partner_ids = [753,2189,758,self.env.user])
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.amount_total < self.env.user.company_id.currency_id._convert(order.company_id.po_triple_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
                if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.user.company_id.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_check()
                else:
                    order.write({'state': 'administration'})
            else:
                order.write({'state': 'management'})
        return True
        super(PurchaseOrder, self).button_confirm()


    def button_list_confirm(self):
        partner_obj = self.env['partner.blacklist']
        exist_supplier = partner_obj.search(
            [('vat', '=', self.partner_id.vat)], limit=1)
        self.message_post(body=('La empresa con RFC <b>%s</b> de Nombre <b>%s</b> Se encuentra en la Lista del 69B con estatus <b>%s</b> y fue autorizado por el Usuario : <b>%s</b> Fecha Publicacion: <b>%s</b>'%(self.partner_id.vat,self.partner_id.name,exist_supplier.situacion_contribuyente,self.env.user.name,exist_supplier.publi_date)),message_type ='email',partner_ids = [753,2189,758,self.env.user])

        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.amount_total < self.env.user.company_id.currency_id._convert(order.company_id.po_triple_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
                if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.user.company_id.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_check()
                else:
                    order.write({'state': 'administration'})
            else:
                order.write({'state': 'management'})
        return True


    @api.onchange('partner_id')
    def onchange_partner_id_warning(self):
        if not self.partner_id:
            return
        warning = {}
        title = False
        message = False

        partner = self.partner_id
        partner_obj = self.env['partner.blacklist']
        exist_supplier = partner_obj.search(
            [('vat', '=', self.partner_id.vat)], limit=1)
        if exist_supplier:
            warning = {
                'title': _('Esta Empresa se encuentra en la lista del 69-B con el estatus %s!'%exist_supplier.situacion_contribuyente),
                'message' : _('Favor de contactar al departamento de contabilidad para seguir el proceso'),
            }
            return {'warning': warning}

        # If partner has no warning, check its company
        if partner.purchase_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.purchase_warn and partner.purchase_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if partner.purchase_warn != 'block' and partner.parent_id and partner.parent_id.purchase_warn == 'block':
                partner = partner.parent_id
            title = _("Warning for %s") % partner.name
            message = partner.purchase_warn_msg
            warning = {
                'title': title,
                'message': message
            }
            if partner.purchase_warn == 'block':
                self.update({'partner_id': False})
            return {'warning': warning}
        return {}
        super(PurchaseOrder, self).onchange_partner_id_warning()

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.onchange('partner_id')
    def onchange_partner_id_warning(self):
        if not self.partner_id:
            return
        warning = {}
        title = False
        message = False
        partner = self.partner_id
        partner_obj = self.env['partner.blacklist']
        exist_supplier = partner_obj.search(
            [('vat', '=', self.partner_id.vat)], limit=1)
        if exist_supplier:
            warning = {
                'title': _('Esta Empresa se encuentra en la lista del 69-B con el estatus %s!'%exist_supplier.situacion_contribuyente),
                'message' : _('Favor de contactar al departamento de contabilidad para seguir el proceso'),
            }
            return {'warning': warning}
        # If partner has no warning, check its company
        if partner.sale_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.sale_warn and partner.sale_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if partner.sale_warn != 'block' and partner.parent_id and partner.parent_id.sale_warn == 'block':
                partner = partner.parent_id
            title = ("Warning for %s") % partner.name
            message = partner.sale_warn_msg
            warning = {
                    'title': title,
                    'message': message,
            }
            if partner.sale_warn == 'block':
                self.update({'partner_id': False, 'partner_invoice_id': False, 'partner_shipping_id': False, 'pricelist_id': False})
                return {'warning': warning}

        if warning:
            return {'warning': warning}
        super(SaleOrder, self).onchange_partner_id_warning()



    def action_confirm(self):
        partner_obj = self.env['partner.blacklist']
        exist_supplier = partner_obj.search(
            [('vat', '=', self.partner_id.vat)], limit=1)
        if exist_supplier:
            self.message_post(
            body=('La empresa con RFC <b>%s</b> de Nombre <b>%s</b> Se encuentra en la Lista del 69B con estatus <b>%s</b> y fue autorizado por el Usuario : <b>%s</b> Fecha Publicacion: <b>%s</b>'%(self.partner_id.vat,self.partner_id.name,exist_supplier.situacion_contribuyente,self.env.user.name,exist_supplier.publi_date)),
            message_type ='email',
            partner_ids = [753,2189,758,self.env.user]
            )


        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True
        super(SaleOrder, self).action_confirm()
