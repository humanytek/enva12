# -*- coding: utf-8 -*-

import logging

from odoo import fields, models,api,_
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class AsmtockLocation(models.Model):
    _inherit = 'stock.location'

    valuation_analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account')


class ASMStockPicking(models.Model):
    _inherit = 'stock.picking'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account')


    @api.multi
    def check_analytic(self):
        self.ensure_one()
        product=self.move_ids_without_package
        if self.picking_type_code == 'outgoing':
            for r in product:
                if not r.analytic_account_id:
                    msg = 'No tiene Cuentas analiticas '
                    raise UserError(_('Cuentas analiticas !\n' + msg))



    @api.multi
    def action_confirm(self):
        res = super(ASMStockPicking, self).action_confirm()
        for order in self:
            order.check_analytic()
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        )

    analytic_product_id = fields.Many2one(
        related='product_id.analytic_account_id',
        string='Analytic Account',
        )





    def _get_analytic_acc_from_move(self):
        analytic_acc = False
        if self.analytic_account_id:
            analytic_acc = self.analytic_account_id.id
        if self.analytic_product_id:
            analytic_acc=self.analytic_product_id.id
        if not analytic_acc and self.picking_id.analytic_account_id:
            analytic_acc = self.picking_id.analytic_account_id.id
        if not analytic_acc and self.location_dest_id.valuation_in_account_id:
            analytic_acc = (self.location_dest_id
                            .valuation_analytic_account_id.id)
        return analytic_acc


    # @api.onchange('product_id')
    # def _analytic(self):
    #     code=False
    #     if self.product_id.name=='Bolt':
    #         code=self.env['account.analytic.account'].search([('code','=','ASML - Cycle')])
    #     if self.product_id.name=='Screw':
    #         code=self.env['account.analytic.account'].search([('code','=','ASML - HOUR')])
    #     return {'value': {'analytic_account_id': code}}


# pylint: disable=R0913
    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        if res and res[0] and res[1][2]:
            analytic_acc = self._get_analytic_acc_from_move()
            res[1][2]['analytic_account_id'] = analytic_acc

        return res

class ProductTemplate(models.Model):
    _inherit='product.template'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        )
