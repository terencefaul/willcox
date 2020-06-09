from odoo import models,fields,api,_


class res_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def get_values(self):
       res = super(res_config_settings, self).get_values()
       param_obj = self.env['ir.config_parameter']
       res.update(group_stock_multi_locations=bool(param_obj.sudo().get_param('stock.group_stock_multi_locations')))
       return res

    @api.multi
    def set_values(self):
       res = super(res_config_settings, self).set_values()
       param_obj = self.env['ir.config_parameter']
       param_obj.sudo().set_param('stock.group_stock_multi_locations', self.group_stock_multi_locations)