from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError, UserError


class detaching_dependent_wizard(models.TransientModel):
    _name = 'detaching.dependent.wizard'
    _description = 'Detaching Dependent'

    partner_id = fields.Many2one('res.partner', string="Medical Aid", required=True)
    medical_aid_plan_id = fields.Many2one('medical.aid.plan', string="Plan")
    plan_option_id = fields.Many2one('medical.aid.plan.option', string="Option ",
                                     domain="[('plan_id','=',medical_aid_plan_id)]")
    medical_aid_no = fields.Char(string="Medical Aid No")

    @api.multi
    def action_detach_dependent(self):
        partner_id = self.env['res.partner'].browse(self._context.get('active_id'))
        if not partner_id.parent_id:
            raise ValidationError(_("Not able to detaching parent record."))
        internal_ref = self.env['ir.sequence'].next_by_code('res.partner')
        partner_id.write({
            'medical_aid_id': self.partner_id.id,
            'option_id': self.medical_aid_plan_id.id,
            'plan_option_id': self.plan_option_id.id,
            'medical_aid_no': self.medical_aid_no,
            'individual_internal_ref': internal_ref,
            'patient_number': internal_ref + "-" + "0",
            'parent_id': False
        })
