from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError

class AccountMove_nova(models.Model):
    _inherit = 'account.move'


    @api.model
    def create(self, vals):

        move = super(AccountMove_nova, self.with_context(check_move_validity=False, partner_id=vals.get('partner_id'))).create(vals)
        move.assert_balanced()
        move._check_lock_date()
        return move
        super(AccountMove_nova, self).create()

    @api.multi
    def write(self, vals):
        if 'line_ids' in vals:
            res = super(AccountMove_nova, self.with_context(check_move_validity=False)).write(vals)
            self.assert_balanced()
            self._check_lock_date()
        else:
            res = super(AccountMove_nova, self).write(vals)
            self._check_lock_date()
        return res
        super(AccountMove_nova, self).write()
