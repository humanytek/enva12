# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

class HumidityPurchase(models.Model):
    _name = 'humidity.tolerance.purchase'
    _description = "Humidity Tolerance Purchase"


    name = fields.Char(
        required=True,
        default='New',
        store=True,
    )

    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Order Purchase',
        store=True,
        ondelete='cascade',
    )

    porcent_tolerance_hum=fields.Integer(

        string = "Porcent Tolerance Humidity",
        store = True

    )

    porcent_tolerance_forb=fields.Integer(

        string = "Porcent Tolerance forbidden",
        store = True

    )

    partner_id=fields.Many2one(
    related='purchase_id.partner_id',
    string='Vendor',
    store=True,
    )

    purchase_name=fields.Char(
    related='purchase_id.name',
    string='Purchase Name',
    store=True,
    )

    order_line_ids = fields.One2many(
    'purchase.order.line',
      'order_id',
      related = 'purchase_id.order_line',
      string = 'Purchase order line',
      readonly = True,

      )

class PurchaseOrder_nova(models.Model):
    _inherit = 'purchase.order'

    humidity_purchase_count=fields.Integer(
    compute='_count_criterios',
    string='Criterios count',

    )
    criterios_occ = fields.Boolean(
    string='Criterios de Compra Occ',
    store=True,
    )



    def _count_criterios(self):
        results = self.env['humidity.tolerance.purchase'].read_group([('purchase_id', 'in', self.ids)], ['purchase_id'], ['purchase_id'])
        dic = {}
        for x in results: dic[x['purchase_id'][0]] = x['purchase_id_count']
        for record in self: record['humidity_purchase_count'] = dic.get(record.id, 0)
