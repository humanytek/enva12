# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseAnalysis(models.Model):
    _inherit = 'purchase.requisition.line'

    responsable = fields.Many2one(
        related='requisition_id.user_id',
        string='Responsable',
        # store=True,
    )

    estado = fields.Selection(
        related='requisition_id.state',
        string='Estado',
    )

    descripcion = fields.Text(
        related='requisition_id.description',
        string='Descripción',
    )

    fecha = fields.Datetime(
        related='requisition_id.purchase_ids.date_order',
        string='Fecha de orden',
    )
