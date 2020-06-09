from odoo import models, fields, api, _


class wizard_stock_take_validate(models.TransientModel):
    _name = 'wizard.stock.take.validate'
    _description = 'Stock Take Validation Wizard'

    stock_take_id = fields.Many2one('stock.take')

    @api.multi
    def validate(self):
        for rec in self:
            if rec.stock_take_id:
                for inv_adjsmnt in rec.stock_take_id.stock_inventory_ids:
                    inv_adjsmnt.action_validate()
                rec.stock_take_id.state = 'validated'

