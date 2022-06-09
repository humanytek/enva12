# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError


class RequisitionPurchase(models.Model):
    _inherit = 'purchase.requisition'

    maintenance_request_id = fields.Many2one(
    'maintenance.request',
    string='Orden de trabajo',
    copy=False
    )
