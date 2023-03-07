# -*- coding: utf-8 -*-

import re
from odoo import models, fields, api
from functools import lru_cache
from odoo.exceptions import UserError

class Invoice_line(models.Model):
    _name = "account.move.line.report.nova"
    _description = "Lineas de Facturas"
    _rec_name = 'aml_date'
    _order = 'aml_date desc'
    _auto = False



    aml_date = fields.Date('Fecha', readonly=True)
    etiqueta = fields.Char('Etiqueta', readonly=True)
    aml_date_maturity = fields.Date('Fecha Vencimiento', readonly=True)
    move_id = fields.Many2one('account.move', 'Asiento Contable', readonly=True)
    default_code = fields.Char('Sku', readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', readonly=True)
    standard_price = fields.Float(related='product_id.standard_price',readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', readonly=True)
    product_uom = fields.Many2one('uom.uom', 'Udm', required=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', readonly=True)
    customer_id = fields.Many2one('res.users', 'Vendedor', readonly=True)
    invoice_origin = fields.Char('Pedido', readonly=True)
    reference = fields.Char('Referencia', readonly=True)
    move_name = fields.Char('Folio', readonly=True)
    quantity = fields.Float('Cantidad', readonly=True,digits="Product Unit of Measure")
    weight = fields.Float('Peso', readonly=True)
    total_weight = fields.Float('Peso Total', readonly=True)
    price_per_kg = fields.Float('Precio x Kg', readonly=True)
    price_unit = fields.Float('Precio Unitario',readonly=True)
    price_subtotal = fields.Float('Subtotal',readonly=True)
    price_total = fields.Float('Precio Total',readonly=True)
    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True)
    credit = fields.Float('Subtotal MX',readonly=True)

    @property
    def _table_query(self):
        return '%s %s %s' % (self._select(), self._from(), self._where())

    @api.model
    def _select(self):
        select_str = """
                SELECT
                    aml.id as id,
                    aml.name as etiqueta,
                    am.id as move_id,
                    aml.move_name,
                    am.ref as reference,
                    aml.date as aml_date,
                    aml.date_maturity as aml_date_maturity,
                    aml.partner_id as partner_id,
                    am.invoice_user_id as customer_id,
                    aml.product_id,
                    p.default_code,
                    p.product_tmpl_id,
                    aml.product_uom_id as product_uom,
                    am.invoice_origin,
                    aml.quantity,
                    p.weight,
                    (aml.quantity*p.weight) as total_weight,
                    aml.price_unit,
                    am.currency_id,
                    aml.price_subtotal,
                    aml.price_total,
                    aml.credit,
                    CASE
                        WHEN (aml.quantity*p.weight)=0 AND aml.credit > 0 THEN 0
                        WHEN (aml.quantity*p.weight)>0 AND aml.credit = 0 THEN 0
                        WHEN (aml.quantity*p.weight)>0 AND aml.credit > 0 THEN (aml.credit/(aml.quantity*p.weight))
                    END price_per_kg
        """
        return select_str

    @api.model
    def _from(self):
        from_str = """
            FROM
            account_move_line aml
            join account_move am on aml.move_id=am.id
            join res_partner partner on partner.id = aml.partner_id
            join res_users customer on customer.id = am.invoice_user_id
            left join product_product p on (aml.product_id=p.id)
            left join product_template t on (p.product_tmpl_id=t.id)
            left join uom_uom line_uom on (line_uom.id=aml.product_uom_id)
            left join uom_uom product_uom on (product_uom.id=t.uom_id)
            left join res_currency rc on rc.id = am.currency_id
        """
        return from_str

    @api.model
    def _where(self):
        where_str = """
            WHERE
                aml.exclude_from_invoice_tab = False AND am.move_type in ('out_invoice') and aml.parent_state='posted'
        """
        return where_str

    @api.model
    def _group_by(self):
        group_by_str = """

        """
        return group_by_str
