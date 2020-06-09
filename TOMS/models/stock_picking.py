from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        if not self._context.get('from_wizard'):
            product_ids = self.move_lines.filtered(lambda l:l.product_id.type == 'consu' and self.picking_type_id.code == 'incoming')
            if product_ids:
                return {
                        'name': _('Receive Product Warning'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'wizard.receive.product',
                        'target': 'new',
                        'context':{'stock_picking_id':self.id}
                    }
            else:
                return super(stock_picking, self).button_validate()
        else:
            return super(stock_picking, self).button_validate()


class StockTakeDMX(models.Model):
    _name = 'stock.take'
    _description = 'Stock take model'

    name = fields.Char()
    note = fields.Text()
    stock_inventory_ids = fields.One2many(
            'stock.inventory',
            'stock_take_id',
            string='Inventory Batches')
    state = fields.Selection([
                             ('draft', 'Draft'),
                             ('in_progress', 'In Progress'),
                             ('validated', 'Validated'),
                             ('cancelled', 'Cancelled'),
                            ],
                            default="draft")

    def start_stock_take(self):
        for rec in self:
            rec.state = 'in_progress'

    def validate_stock_take(self):
        return {
            'name': 'Validate Stock Take',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.stock.take.validate',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_stock_take_id': self.id,
            }
        }

    def cancel_stock_take(self):
        for rec in self:
            for inv_adjsmnt in rec.stock_inventory_ids:
                inv_adjsmnt.action_cancel_draft
            rec.state = 'cancelled'


class StockInventoryDMX(models.Model):
    _inherit = 'stock.inventory'

    stock_take_id = fields.Many2one(
            'stock.take',
            string='Stock Take')


class StockInventoryLineDMX(models.Model):
    _inherit = 'stock.inventory.line'

    _debug= True

    def log(self, msg):
        if self._debug:
            _logger.info(msg)

    @api.depends('product_qty', 'theoretical_qty', 'value')
    def _get_total_value(self):
        for rec in self:
            rec.variance= rec.product_qty - rec.theoretical_qty
            rec.total_value = rec.value * rec.variance

    variance = fields.Float(string='Variance', store=True,
            compute=_get_total_value,
        )
    value = fields.Float(string='Unit Value',
            related='product_id.standard_price',
            store=True)
    total_value = fields.Float(string='Total Value',
            compute=_get_total_value,
            store=True,
            readonly=True)
    stock_name = fields.Char(string='Stock Name',
            store=True,
            readonly=True)
