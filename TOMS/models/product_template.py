from odoo import models, fields, _


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    code = fields.Char(string="Code")


class product_template(models.Model):
    _inherit = 'product.template'

    saoa_code_id = fields.Many2one('saoa.codes', string="SAOA Code")
    ppn1_code_id = fields.Many2one('ppn1.codes', string="PPN1 Code")
    common_icd_id = fields.Many2one('icd.codes', string="Common ICD")
    nappi_code_id = fields.Many2one('nappi.codes', string="NAPPI Code")
    lens_material_id = fields.Many2one('lens.material', string="Lens Material")
    lens_type_id = fields.Many2one('lens.type', string="Lens Type")
    old_code_id = fields.Many2one('old.codes', string="Old Code")


class lens_material(models.Model):
    _name = 'lens.material'
    _description = 'Lense Material'

    name = fields.Char(string="Lens Material")


class lens_type(models.Model):
    _name = 'lens.type'
    _description = 'Lense Type'

    name = fields.Char(string="Lens Type")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
