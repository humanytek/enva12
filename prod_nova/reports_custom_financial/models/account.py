# -*- coding: utf-8 -*-

import time
import math
import re
import logging

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, remove_accents
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


_logger = logging.getLogger(__name__)

class AccountAccount(models.Model):
    _inherit = "account.account"

    group_finantial_id = fields.Many2one('account.group.nova',string = 'Grupo Financiero',)


class AccountGroup(models.Model):
    _name = "account.group.nova"
    _description = 'Account Group Financial'
    _parent_store = True
    _order = 'code_prefix'

    parent_id = fields.Many2one('account.group.nova', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    name = fields.Char(required=True)
    code_prefix = fields.Char()

    def name_get(self):
        result = []
        for group in self:
            name = group.name
            if group.code_prefix:
                name = group.code_prefix + ' ' + name
            result.append((group.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            criteria_operator = ['|'] if operator not in expression.NEGATIVE_TERM_OPERATORS else ['&', '!']
            domain = criteria_operator + [('code_prefix', '=ilike', name + '%'), ('name', operator, name)]
        group_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(group_ids).name_get()
