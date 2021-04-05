# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import time
from odoo import api, models,fields, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.addons.web.controllers.main import clean_action
_logger = logging.getLogger(__name__)


class ReportsSales(models.AbstractModel):
    _name = "report.sales.nova"
    _description = "Reports Sales"
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    # filter_all_entries = False

    def _get_columns_name(self, options):
        return [
        {'name': ''}, {'name': _('VOLUMEN PRESUPUESTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('VOLUMEN REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('TENDENCIA'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PROMEDIO AÑO ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('MES AÑO ANTERIOR'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO x KG PPTO'), 'class': 'number', 'style': 'white-space:nowrap;'},
        {'name': _('PRECIO x KG REAL'), 'class': 'number', 'style': 'white-space:nowrap;'},
        ]




    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        return lines

    @api.model
    def _get_report_name(self):
        return _('Tendencia de Ventas')
