# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    l10n_mx_edi_iedu_id = fields.Many2one(
        'res.partner', string='Student', help="Student information for IEDU "
        "complement:\n Make sure that the student have set CURP.")
