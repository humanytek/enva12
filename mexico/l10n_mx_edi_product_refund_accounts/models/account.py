from odoo import models, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.v8
    def get_invoice_line_account(self, type, product, fpos, company):
        if type not in ('out_refund', 'in_refund'):
            return super(AccountInvoiceLine, self).get_invoice_line_account(
                type, product, fpos, company)
        accounts = product.product_tmpl_id.get_product_accounts(fpos)
        account_map = {
            'out_refund': 'income_refund',
            'in_refund': 'expense_refund',
        }
        return accounts[account_map[type]]
