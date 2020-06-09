from odoo import fields, models, api


class hway_sport(models.Model):
    _name = 'hway.sport'
    _description = 'HWAY Sport'
    _order = 'name'

    name = fields.Char(string='Name', required=False)

class hway_hobby(models.Model):
    _name = 'hway.hobby'
    _description = 'HWAY hobby'
    _order = 'name'

    name = fields.Char(string='Name', required=False)

class hway_doyou(models.Model):
    _name = 'hway.doyou'
    _description = 'HWAY doyou'
    _order = 'name'

    name = fields.Char(string='Name', required=False)

class hway_doesyour(models.Model):
    _name = 'hway.doesyour'
    _description = 'HWAY doesyour'
    _order = 'name'

    name = fields.Char(string='Name', required=False)

