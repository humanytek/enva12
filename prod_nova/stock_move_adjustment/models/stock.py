# -*- coding: utf-8 -*-

import logging
from odoo.tools.float_utils import float_round, float_is_zero
from odoo import api, fields, models, _


class stock_picking(models.Model):
    _inherit = 'stock.picking'


    def _compute_fecha_tipo_cambio_requerida(self):
        sale_order=self.env['purchase.order'].search([('name','=',self.origin)])
        sale_order=sale_order[0] if sale_order else False

        if sale_order and sale_order.currency_id != self.company_id.currency_id and self.picking_type_id.code=='incoming':
            self.fecha_tipo_cambio_requerida=True
        else:
            self.fecha_tipo_cambio_requerida=False
        return


    fecha_tipo_cambio = fields.Date(
        string='Fecha Tipo Cambio'
    )
    fecha_tipo_cambio_requerida=fields.Boolean(
        string="Requiere la fecha del tipo de cambio",
        compute=_compute_fecha_tipo_cambio_requerida

    )


class StockMove(models.Model):
    _inherit = 'stock.move'



    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        self.ensure_one()
        if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.price_unit
            if line.taxes_id:
                qty = line.product_qty or 1
                price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=qty)['total_void']
                # price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=1.0)['total_excluded']
                price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                # The date must be today, and not the date of the move since the move move is still
                # in assigned state. However, the move date is the scheduled date until move is
                # done, then date of actual move processing. See:
                # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
                price_unit = order.currency_id._convert(
                    price_unit, order.company_id.currency_id, order.company_id, self.picking_id.fecha_tipo_cambio, round=False)
            return price_unit
        return super(StockMove, self)._get_price_unit()


    # #version odoo 12
    # def _get_price_unit(self):
    #     """ Returns the unit price for the move"""
    #     self.ensure_one()
    #     if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
    #         line = self.purchase_line_id
    #         order = line.order_id
    #         price_unit = line.price_unit
    #         if line.taxes_id:
    #             price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=1.0)['total_excluded']
    #         if line.product_uom.id != line.product_id.uom_id.id:
    #             price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
    #         if order.currency_id != order.company_id.currency_id:
    #             price_unit = order.currency_id._convert(
    #                 price_unit, order.company_id.currency_id, order.company_id, self.picking_id.fecha_tipo_cambio, round=False)
    #         return price_unit
    #     return super(StockMove, self)._get_price_unit()




    # version odoo 10
    # @api.multi
    # def _get_price_unit(self):
    #     """ Returns the unit price to store on the quant """
    #     if self.picking_id.fecha_tipo_cambio and self.picking_id.fecha_tipo_cambio_requerida:
    #         if self.purchase_line_id:
    #             order = self.purchase_line_id.order_id
    #             #if the currency of the PO is different than the company one, the price_unit on the move must be reevaluated
    #             #(was created at the rate of the PO confirmation, but must be valuated at the rate of stock move execution)
    #             if order.currency_id != self.company_id.currency_id:
    #                 #we don't pass the move.date in the compute() for the currency rate on purpose because
    #                 # 1) get_price_unit() is supposed to be called only through move.action_done(),
    #                 # 2) the move hasn't yet the correct date (currently it is the expected date, after
    #                 #    completion of action_done() it will be now() )
    #                 price_unit = self.purchase_line_id.with_context(date=self.picking_id.fecha_tipo_cambio)._get_stock_move_price_unit()
    #                 self.write({'price_unit': price_unit})
    #                 return price_unit
    #         return self.price_unit
    #     return super(StockMove, self)._get_price_unit()
