from odoo import models, fields, api, _


class codes_model(models.Model):
    _name = 'medical.aid.plan'
    _description = 'Medical Aid Plan'

    code = fields.Selection([('SAOA', 'SAOA'),
                             ('PPN1', 'PPN1'),
                             ], string="Code", default="saoa")
    name = fields.Char(string="Medical Aid Plan")
    plan_code = fields.Char(string="Plan Code")
    medical_aid_id = fields.Many2one('res.partner', string="Medical Aid")
    comment = fields.Text(string="Comment")


class MedicalAidPlanOptions(models.Model):
    _name = 'medical.aid.plan.option'
    _description = 'Medical Aid Plan Option'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    plan_id = fields.Many2one('medical.aid.plan', 'Plan')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    comment = fields.Text(string="Comment")
    active = fields.Boolean(string="Active", default=True)
    destination_code = fields.Char(string="Destination Code")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
