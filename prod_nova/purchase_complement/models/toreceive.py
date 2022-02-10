# -*- coding: utf-8 -*-
from odoo import fields, models


class Productstoreceive(models.Model):
    _inherit = 'stock.move'

    purchase_agreement_id = fields.Many2one(
        # related='picking_type_id.name',
        related='picking_id.purchase_id.requisition_id',
        string='Acuerdo Compra',
    )

    purchase_agreement_provider = fields.Many2one(
        related='picking_id.purchase_id.partner_id',
        string='Proveedor',
    )

    purchase_agreement_representative_provider = fields.Many2one(
        related='picking_id.purchase_id.user_id',
        string='Representante Proveedor',
    )

    purchase_agreement_date_order = fields.Datetime(
        related='picking_id.purchase_id.date_order',
        string='Fecha OC',
    )

    purchase_agreement_date_requisition = fields.Date(
        related='picking_id.purchase_id.requisition_id.ordering_date',
        string='Fecha Requi',
    )
