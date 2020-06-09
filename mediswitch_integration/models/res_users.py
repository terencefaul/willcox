from odoo import models, api, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    op_number = fields.Char(string="OP Number")
