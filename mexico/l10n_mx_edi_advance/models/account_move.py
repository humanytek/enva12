# -*- coding: utf-8 -*-
from odoo import api, models, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        """Create a new journal entry if one invoice is an advance"""
        res = super(AccountMoveLine, self).reconcile(
            writeoff_acc_id, writeoff_journal_id)
        if not self.mapped('payment_id'):
            return res
        # create a magic entry to allow handle advances as outstanding payments
        # only create the entry is the advance is paid.
        self._create_advance_magic_entry()
        return res

    @api.multi
    def remove_move_reconcile(self):
        """ Undo a reconciliation """
        move_obj = self.env['account.move']
        adv_journal = self.mapped('company_id.l10n_mx_edi_journal_advance_id')
        for invoice in self.mapped('payment_id.invoice_ids'):
            moves = move_obj.search([
                ('ref', '=like', '% '+invoice.move_id.name),
                ('journal_id', '=', adv_journal.id)])
            moves.button_cancel()
            moves.unlink()
        return super(AccountMoveLine, self).remove_move_reconcile()

    @api.multi
    def _create_advance_magic_entry(self, amount=False, currency=False):
        move_obj = self.env['account.move']
        partner_obj = self.env['res.partner']
        aml_obj = self.with_context(check_move_validity=False)
        for adv in self.mapped('invoice_id').filtered(
                lambda r: r._l10n_mx_edi_is_advance() and r.state == 'paid'):
            adv_journal = adv.company_id.l10n_mx_edi_journal_advance_id
            adv_product = adv.company_id.l10n_mx_edi_product_advance_id
            amount_total = amount or adv.amount_total
            currency_id = currency or adv.currency_id
            partner = partner_obj._find_accounting_partner(adv.partner_id)
            debit, credit, amount_currency, dummy = aml_obj.with_context(
                date=adv.date)._compute_amount_fields(
                    amount_total, currency_id, adv.company_id.currency_id)
            amount_currency = currency_id._convert(
                amount_total, adv_journal.currency_id, adv.company_id,
                adv.date) if adv_journal.currency_id else 0
            payment = self.mapped('payment_id')
            magic_move = move_obj.create({
                'date': adv.date,
                'journal_id': adv_journal.id,
                'ref': '%s %s' % (payment.communication or payment.name,
                                  adv.move_id.name),
                'company_id': adv.company_id.id,
                'narration': _(
                    'This is a Journal Entry to handle advance payments with '
                    'a receivable account and use the payment widget of '
                    'outstanding credit.\n'
                    'This advance is the CFDI: %s, invoice_id: %s.'
                ) % (adv.l10n_mx_edi_cfdi_uuid, adv.id),
            })
            aml_obj.create({
                'partner_id': partner.id,
                'invoice_id': adv.id,
                'move_id': magic_move.id,
                'debit': debit,
                'credit': credit,
                'amount_currency': amount_currency or False,
                'journal_id': adv_journal.id,
                'currency_id': adv_journal.currency_id.id,
                'account_id': adv_product.property_account_income_id.id,
                'name': 'Anticipo del bien o servicio',
            })
            aml_obj.create({
                'partner_id': partner.id,
                'invoice_id': adv.id,
                'move_id': magic_move.id,
                'debit': credit,
                'credit': debit,
                'amount_currency': -amount_currency or False,
                'journal_id': adv_journal.id,
                'currency_id': adv_journal.currency_id.id,
                'account_id': adv_product.property_account_expense_id.id,
                'name': 'Anticipo del bien o servicio',
            })
            magic_move.action_post()
