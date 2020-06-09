from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    calendar_bg_color = fields.Char(string="Calendar Background Color")
    calendar_text_color = fields.Char(string="Calendar Text Color")
    display_roster_view = fields.Boolean(string="Display in roster view", default=True)
    active_roster_view = fields.Boolean(string="Active in roster view", default=True)
