from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    group_l10n_mx_edi_cancellation_with_reversal_move = fields.Boolean(
        string='Enable cancellation with reversal move',
        implied_group='l10n_mx_edi_cancellation.group_cancellation_with_reversal_move',  # noqa
        readonly=False, help='Enable the cancellation of payments from '
        'previous periods with reversal entries.')
