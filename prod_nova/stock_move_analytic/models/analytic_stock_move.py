# -*- coding: utf-8 -*-

import logging

from odoo import fields, models,api,_
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class AsmtockLocation(models.Model):
    _inherit = 'stock.location'

    valuation_analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        )


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
            if self.location_id.id != 21:
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

class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': _("Return of %s") % self.picking_id.name,
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id})
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self.picking_id},
            subtype_id=self.env.ref('mail.mt_note').id)
        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed."))
            # TODO sle: float_is_zero?
            if return_line.quantity:
                returned_lines += 1
                vals = self._prepare_move_default_values(return_line, new_picking)
                r = return_line.move_id.copy(vals)
                vals = {}

                # +--------------------------------------------------------------------------------------------------------+
                # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
                # |              | returned_move_ids              ↑                                  | returned_move_ids
                # |              ↓                                | return_line.move_id              ↓
                # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
                # +--------------------------------------------------------------------------------------------------------+
                move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
                move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | return_line.move_id]
                vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                r.write(vals)
        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        return new_picking.id, picking_type_id
        super(ReturnPicking, self)._create_returns()
