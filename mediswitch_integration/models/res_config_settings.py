from odoo import fields, api, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    production_url = fields.Char(string="Production URL")
    test_url = fields.Char(string="Test URL")
    claim_reversal = fields.Boolean(string="Claims & Reversals")
    benefit_check = fields.Boolean(string="Benefit Check")
    membership_status_validation = fields.Boolean(string="Membership Status Validation (MSV)")
    electronic_remittance_advice = fields.Boolean(string="Electronic Remittance Advice (eRA)")
    practice_number = fields.Char(string="Practice Number")
    practice_name = fields.Char(string="Practice Name")
    for_what=fields.Selection([('test','Testing'),('production','Production')],string="For")
    user_name_test=fields.Char(string="UserName Test")
    user_name_production = fields.Char(string="UserName Production")
    password_test =fields.Char(string="Password Test")
    password_production = fields.Char(string="Password Production")
    package_test=fields.Char(string="Package Name Test")
    package_production=fields.Char(string="Package Name Production")
    txtype_test=fields.Char(string="Tx Type Test")
    txtype_production=fields.Char(string="Tx Type Production")
    mode_test=fields.Char(string="Mode Test")
    mode_production=fields.Char(string="Mode Production")
    txversion_test=fields.Char(string="Tx Version Test")
    txversion_production=fields.Char(string="Tx Version Production")


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter']
        res.update({
            'production_url': param_obj.sudo().get_param('mediswitch_integration.production_url'),
            'test_url': param_obj.sudo().get_param('mediswitch_integration.test_url'),
            'claim_reversal': param_obj.sudo().get_param('mediswitch_integration.claim_reversal'),
            'benefit_check': param_obj.sudo().get_param(
                'mediswitch_integration.benefit_check'),
            'membership_status_validation': param_obj.sudo().get_param('mediswitch_integration.membership_status_validation'),
            'electronic_remittance_advice': param_obj.sudo().get_param('mediswitch_integration.electronic_remittance_advice'),
            'practice_number': param_obj.sudo().get_param('mediswitch_integration.practice_number'),
            'practice_name': param_obj.sudo().get_param('mediswitch_integration.practice_name'),
            'for_what':param_obj.sudo().get_param('mediswitch_integration.for_what'),
            'user_name_test':param_obj.sudo().get_param('mediswitch_integration.user_name_test'),
            'user_name_production':param_obj.sudo().get_param('mediswitch_integration.user_name_production'),
            'password_test':param_obj.sudo().get_param('mediswitch_integration.password_test'),
            'password_production':param_obj.sudo().get_param('mediswitch_integration.password_production'),
            'package_test':param_obj.sudo().get_param('mediswitch_integration.package_test'),
            'package_production':param_obj.sudo().get_param('mediswitch_integration.package_production'),
            'txtype_test':param_obj.sudo().get_param('mediswitch_integration.txtype_test'),
            'txtype_production':param_obj.sudo().get_param('mediswitch_integration.txtype_production'),
            'mode_test':param_obj.sudo().get_param('mediswitch_integration.mode_test'),
            'mode_production':param_obj.sudo().get_param('mediswitch_integration.mode_production'),
            'txversion_test':param_obj.sudo().get_param('mediswitch_integration.txversion_test'),
            'txversion_production':param_obj.sudo().get_param('mediswitch_integration.txversion_production'),
        })
        return res

    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param_obj = self.env['ir.config_parameter']
        param_obj.sudo().set_param('mediswitch_integration.production_url', self.production_url)
        param_obj.sudo().set_param('mediswitch_integration.test_url', self.test_url)
        param_obj.sudo().set_param('mediswitch_integration.claim_reversal', self.claim_reversal)
        param_obj.sudo().set_param('mediswitch_integration.benefit_check',
                                   self.benefit_check)
        param_obj.sudo().set_param('mediswitch_integration.membership_status_validation',
                                   self.membership_status_validation)
        param_obj.sudo().set_param('mediswitch_integration.electronic_remittance_advice',
                                   self.electronic_remittance_advice)
        param_obj.sudo().set_param('mediswitch_integration.practice_number',
                                   self.practice_number)
        param_obj.sudo().set_param('mediswitch_integration.practice_name',
                                   self.practice_name)
        param_obj.sudo().set_param('mediswitch_integration.for_what',self.for_what)
        param_obj.sudo().set_param('mediswitch_integration.user_name_test',self.user_name_test)
        param_obj.sudo().set_param('mediswitch_integration.user_name_production',self.user_name_production)
        param_obj.sudo().set_param('mediswitch_integration.password_test',self.password_test)
        param_obj.sudo().set_param('mediswitch_integration.password_production',self.password_production)
        param_obj.sudo().set_param('mediswitch_integration.package_test',self.package_test)
        param_obj.sudo().set_param('mediswitch_integration.package_production',self.package_production)
        param_obj.sudo().set_param('mediswitch_integration.txtype_test',self.txtype_test)
        param_obj.sudo().set_param('mediswitch_integration.txtype_production',self.txtype_production)
        param_obj.sudo().set_param('mediswitch_integration.mode_test',self.mode_test)
        param_obj.sudo().set_param('mediswitch_integration.mode_production',self.mode_production)
        param_obj.sudo().set_param('mediswitch_integration.txversion_test',self.txversion_test)
        param_obj.sudo().set_param('mediswitch_integration.txversion_production',self.txversion_production)
        return res
