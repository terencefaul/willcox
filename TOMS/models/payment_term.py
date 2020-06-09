from odoo import models, fields, api, _
from odoo.exceptions import Warning


class account_payment_term(models.Model):
    _inherit = 'account.payment.term'

    @api.multi
    def unlink(self):
        rec_id_immediate = self.env.ref("account.account_payment_term_immediate")
        rec_id_15day = self.env.ref("account.account_payment_term_15days")
        for each in self:
            if each.id in [rec_id_immediate.id, rec_id_15day.id]:
                raise Warning(_('You cannot delete this payment method.'))
        return super(account_payment_term, self).unlink()
