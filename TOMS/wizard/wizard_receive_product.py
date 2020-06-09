from odoo import models, fields, api, _


class wizard_receive_product(models.TransientModel):
    _name = 'wizard.receive.product'
    _description = 'Wizard Recieve Product'

    @api.multi
    def wizard_receive_product_warning(self):
        stock_picking_id = self.env['stock.picking'].browse(self._context.get('stock_picking_id'))
        return stock_picking_id.with_context({'from_wizard':True}).button_validate()