# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.translate import _
from odoo.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError



class AccountFollowupReport(models.AbstractModel):
    _inherit = 'account.followup.report'


    @api.model
    def print_followups(self, records):
        """
        Print one or more followups in one PDF
        records contains either a list of records (come from an server.action) or a field 'ids' which contains a list of one id (come from JS)
        """
        res_ids = records['ids'] if 'ids' in records else records.ids  # records come from either JS or server.action
        # for partner in self.env['res.partner'].browse(res_ids):
        #     partner.message_post(body=_('Follow-up letter printed'))
        return self.env.ref('account_reports.action_report_followup').report_action(res_ids)
        super(AccountFollowupReport, self).print_followups()
