from odoo import api, models
from odoo.tools import float_round


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _l10n_mx_edi_create_cfdi_values(self):
        res = super(AccountInvoice, self)._l10n_mx_edi_create_cfdi_values()
        precision_digits = res['decimal_precision'] if res[
            'currency_name'] == 'MXN' else 4
        subtotal_wo_discount = lambda l: float_round(
            l.price_subtotal / (1 - l.discount/100) if l.discount != 100 else
            l.price_unit * l.quantity, int(precision_digits))
        res['subtotal_wo_discount'] = subtotal_wo_discount
        return res
