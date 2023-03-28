# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Indicators(models.Model):
    _name = 'indicators.nova'
    _description = "Indicators"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char(
        required=True,
        default='New',
        store=True,
    )
    back_order = fields.Float(
        string='Back Order ',
        store=True,
    )
    back_log = fields.Float(
        string='Back Log ',
        store=True,
    )
    ton_fosber = fields.Float(
        string='Ton Fosber ',
        store=True,
    )
    mezcla_prom = fields.Float(
        string="Average Mix",
        store=True,
    )
    paper_weight = fields.Float(
        string="Paper Weight",
        store=True,
    )
    consumed_paper = fields.Float(
        string="Consumed Paper",
        store=True,
    )
    controllable_trim = fields.Float(
        string="Controllable Trim",
        store=True,
    )
    finished_warehouse = fields.Float(
        string="Finished Warehouse",
        store=True
    )
    total_waste = fields.Float(
        string="Total Waste",
        store=True,
    )
    paca_waste = fields.Float(
        string="Paca Waste",
        store=True,
    )
    total_waste_formula = fields.Float(
        string="Total Waste Formula",
        store=True,
    )
    total_rolls = fields.Float(
        string="Total Rolls",
        store=True,
    )
    ton_lam = fields.Float(
        string="Tons Lamina",
        store=True,
    )
    invoiced_lam = fields.Float(
        string="Real Invoiced Lam",
        store=True,
    )
    other_receipts = fields.Float(
        string="Other Receipts",
        store=True,
    )
    project = fields.Float(
        string="Project",
        store=True,
    )
    indicator_date= fields.Date(
        required=True,
        string='Indicator Date',
        tracking=True,
        default=fields.Date.context_today,
    )
    price_lam = fields.Float(
        string="Average Price Lam",
        store=True,
    )
    tons_shipment = fields.Float(
        string="Tons Shipment",
        store=True,
    )
    tons_paper = fields.Float(
        string="Tons Paper ",
        store=True,
    )
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('indicators.nova') or '/'
        return super(Indicators, self).create(vals)
