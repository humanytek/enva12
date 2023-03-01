# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare, float_round
from odoo.osv import expression

from collections import defaultdict


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    def _compute_allowed_mo_ids(self):
        # the function remains as a stable fix patch that was removed in master
        self.allowed_mo_ids = False
        super(MrpUnbuild, self)._compute_allowed_mo_ids()