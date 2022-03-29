# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
class AccountInvoice(models.Model):
    _inherit = 'account.move'


    def _get_currency_rate_date(self):
        return self.date_invoice or self.date


    def _get_accounting_date(self, invoice_date, has_tax):
        """Get correct accounting date for previous periods, taking tax lock date into account.

        When registering an invoice in the past, we still want the sequence to be increasing.
        We then take the last day of the period, depending on the sequence format.
        If there is a tax lock date and there are taxes involved, we register the invoice at the
        last date of the first open period.

        :param invoice_date (datetime.date): The invoice date
        :param has_tax (bool): Iff any taxes are involved in the lines of the invoice
        :return (datetime.date):
        """
        tax_lock_date = self.company_id.tax_lock_date
        today = fields.Date.today()
        if invoice_date and tax_lock_date and has_tax and invoice_date <= tax_lock_date:
            invoice_date = tax_lock_date + timedelta(days=1)

        if self.is_sale_document(include_receipts=True):
            return invoice_date
        elif self.is_purchase_document(include_receipts=True):
            return invoice_date
        return invoice_date
        super (AccountInvoice, self)._get_accounting_date()

    # def action_move_create(self):
    #     """ Creates invoice related analytics and financial move lines """
    #     for inv in self:
    #         today=fields.Date.context_today(self)
    #         if not inv.date:
    #             inv.date=today
    #
    #         if (inv.currency_id.id != inv.company_id.currency_id.id) :
    #             fecha_t_cambio=inv.date_invoice or today
    #             rate=self.company_id.currency_id._get_rate(fecha_t_cambio)
    #             # if not rate or rate == 1.0 :
    #             if not rate :
    #                 raise ValidationError(_('An exchange rate for invoice date : %s must be specified ' % fecha_t_cambio))
    #     res=super (AccountInvoice, self).action_move_create()
    #     return res



class Currency(models.Model):
    _inherit = "res.currency"


    def _get_rate(self, date=fields.Date.today()):
        self.ensure_one()
        company_id = self._context.get('company_id') or self.env['res.users']._get_company().id
        # the subquery selects the last rate before 'date' for the given currency/company
        query = """SELECT c.id, (SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name >= %s::date AND r.name < (%s::date + '1 day'::interval)
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1) AS rate
                   FROM res_currency c
                   WHERE c.id = %s"""
        self._cr.execute(query, (date, date,company_id, self.id))
        currency_rate = dict(self._cr.fetchall())
        res = currency_rate.get(self.id) or False
        return res
