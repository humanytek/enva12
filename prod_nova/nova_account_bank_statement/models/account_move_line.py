# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re, float_is_zero
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.osv import expression

from datetime import date, timedelta
from collections import defaultdict
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings

TERM_PAYMENTS = [
    ('contado', 'Contado'),
    ('credito', 'Credito'),
]

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    term_payment_nova = fields.Selection(TERM_PAYMENTS,
    'Tipo de Pago', store=True)

    is_project = fields.Boolean(
    string='Es Proyecto?',
    store=True,
    )