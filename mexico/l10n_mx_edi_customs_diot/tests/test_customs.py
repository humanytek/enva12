# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase


class EdiCustoms(TransactionCase):
    def setUp(self):
        super(EdiCustoms, self).setUp()
        self.customs = self.env['l10n_mx_edi.customs']

    def test_revert_custom(self):
        custom = self.create_customs()
        custom.approve_custom()
        self.assertEquals('confirmed', custom.state,
                          'State not updated correctly')
        invoice = custom.sat_invoice_id
        payment = invoice.payment_move_line_ids.mapped('payment_id')
        invoice.journal_id.update_posted = True
        custom.revert_custom()
        self.assertEquals('draft', custom.state,
                          'The custom not was reverted.')
        self.assertEquals('cancel', invoice.state,
                          'The invoice not was cancelled.')
        self.assertEquals('cancelled', payment.state,
                          'The payment not was cancelled.')

    def create_customs(self):
        partner = self.env.ref('base.res_partner_12')
        account_dta = self.env['account.account'].create({
            'code': '601.73.002',
            'name': 'DTA',
            'user_type_id': self.ref('account.data_account_type_expenses'),
        })
        bank_journal = self.env['account.journal'].create({
            'name': 'My bank',
            'code': 'MB',
            'type': 'bank',
            'update_posted': True,
        })
        return self.customs.create({
            'name': '19 24 34 9000104',
            'date': self.env['l10n_mx_edi.certificate'].sudo().get_mx_current_datetime().date(),  # noqa
            'operation': 'IMP',
            'key_custom': 'A1',
            'regime': 'IMD',
            'sat_partner_id': partner.id,
            'dta': 4287.00,
            'account_dta_id': account_dta.id,
            'journal_payment_id': bank_journal.id,
        })
