# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools.misc import format_date

from dateutil.relativedelta import relativedelta
from itertools import chain


class report_account_aged_partner(models.AbstractModel):
    _inherit = 'account.aged.partner'

    date_maturity = fields.Date(group_operator='max')
    date_move = fields.Date(group_operator='max')
    invoice_date = fields.Date(group_operator='max')
    date_maturity = fields.Date(group_operator='max')
    amount_total = fields.Monetary(string='Monto')
    invoice_origin = fields.Char(string='Pedido')
    currency_name = fields.Char(string='Moneda')
    rate_currency = fields.Monetary(string='TC')

    @api.model
    def _get_sql(self):
        options = self.env.context['report_options']
        query = ("""
            SELECT
                {move_line_fields},
                account_move_line.partner_id AS partner_id,
                partner.name AS partner_name,
                COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                account_move_line.payment_id AS payment_id,
                COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                account_move_line.expected_pay_date AS expected_pay_date,
                move.move_type AS move_type,
                move.name AS move_name,
                rc.name AS currency_name,
                move.date AS date_move,
                move.invoice_date AS invoice_date,
                account_move_line.date_maturity as date_maturity,
                move.amount_total AS amount_total,
                  (CASE
                      WHEN move.amount_total >= 1  THEN %(sign)s *(move.amount_total_signed/move.amount_total)
                      WHEN move.amount_total = 0 THEN 0
                  END) AS rate_currency,
                move.invoice_origin AS invoice_origin,
                journal.code AS journal_code,
                COALESCE(NULLIF(account_tr.value, ''), account.name) as account_name,
                account.code AS account_code,""" + ','.join([("""
                CASE WHEN period_table.period_index = {i}
                THEN %(sign)s * ROUND((
                    account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
                ) * currency_table.rate, currency_table.precision)
                ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
            FROM account_move_line
            JOIN account_move move ON account_move_line.move_id = move.id
            JOIN account_journal journal ON journal.id = account_move_line.journal_id
            JOIN account_account account ON account.id = account_move_line.account_id
            LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
            LEFT JOIN res_currency rc on rc.id = account_move_line.currency_id
            LEFT JOIN ir_property trust_property ON (
                trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                AND trust_property.name = 'trust'
                AND trust_property.company_id = account_move_line.company_id
            )
            JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN LATERAL (
                SELECT part.amount, part.debit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date)s
            ) part_debit ON part_debit.debit_move_id = account_move_line.id
            LEFT JOIN LATERAL (
                SELECT part.amount, part.credit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date)s
            ) part_credit ON part_credit.credit_move_id = account_move_line.id
            JOIN {period_table} ON (
                period_table.date_start IS NULL
                OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
            )
            AND (
                period_table.date_stop IS NULL
                OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
            )
            LEFT JOIN ir_translation account_tr ON (
                account_tr.name = 'account.account,name'
                AND account_tr.res_id = account.id
                AND account_tr.type = 'model'
                AND account_tr.lang = %(lang)s
            )
            WHERE account.internal_type = %(account_type)s
            GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
                     period_table.period_index, currency_table.rate, currency_table.precision, account_name, rc.name
            HAVING ROUND(account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0), currency_table.precision) != 0
        """).format(
            move_line_fields=self._get_move_line_fields('account_move_line'),
            currency_table=self.env['res.currency']._get_query_currency_table(options),
            period_table=self._get_query_period_table(options),
        )
        params = {
            'account_type': options['filter_account_type'],
            'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
            'date': options['date']['date_to'],
            'lang': self.env.user.lang or get_lang(self.env).code,
        }
        return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)
        super(report_account_aged_partner, self)._get_sql()

    ####################################################
    # COLUMNS/LINES
    ####################################################
    @api.model
    def _get_column_details(self, options):
        return [
            self._header_column(),
            self._field_column('journal_code', name=_("Journal")),
            self._field_column('account_name', name=_("Account")),
            self._field_column('report_date'),
            self._field_column('invoice_date',name=_("Fecha Factura")),
            self._field_column('date_move',name=_("Fecha Contable")),
            self._field_column('date_maturity',name=_("Fecha Vencimiento")),
            self._field_column('expected_pay_date',name=_("Fecha Esperada")),
            self._field_column('amount_total',name=_("Monto")),
            self._field_column('currency_name',name=_("Moneda")),
            self._field_column('rate_currency',name=_("TC")),
            self._field_column('invoice_origin',name=_("Origen")),
            self._field_column('period0', name=_("As of: %s") % format_date(self.env, options['date']['date_to'])),
            self._field_column('period1', sortable=True),
            self._field_column('period2', sortable=True),
            self._field_column('period3', sortable=True),
            self._field_column('period4', sortable=True),
            self._field_column('period5', sortable=True),
            self._custom_column(  # Avoid doing twice the sub-select in the view
                name=_('Total'),
                classes=['number'],
                formatter=self.format_value,
                getter=(lambda v: v['period0'] + v['period1'] + v['period2'] + v['period3'] + v['period4'] + v['period5']),
                sortable=True,
            ),
        ]
        super(report_account_aged_partner, self)._get_column_details()
