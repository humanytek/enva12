# Copyright 2018 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    l10n_mx_edi_customs_id = fields.Many2one(
        'l10n_mx_edi.customs', 'Custom',
        help='Custom in which this invoice income in the company.')
    l10n_mx_edi_customs_extra_id = fields.Many2one(
        'l10n_mx_edi.customs', 'Customs Extra',
        help='Custom in which this invoice income in the company.')
