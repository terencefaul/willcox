from odoo import api, fields, models, _


class activity_statement_config_setting(models.TransientModel):
    _inherit = 'res.config.settings'

    automatic_statement = fields.Boolean(string="Turn On automatic statements")
    cron_next_call_date = fields.Integer(string="Cron Next Call Date")
    send_to_options = fields.Selection([
                                ('send_to_all','Send to All'),
                                ('outstanding_balance_only','Outstanding Balance Only')
                                ], string="Send Options")
    statement_period = fields.Selection([
                                                 ('current_fiscal_year', 'Current Fiscal Year'),
                                                 ('current_quarter', 'Current Quarter'),
                                                 ('current_month', 'Current Month'),
                                                 ], string="Default Statement Period")
    mode = fields.Selection([
                            ('Production','Production'),
                            ('Test','Test')
                            ])
    test_email_address = fields.Char(string="Test Email Address")

    def get_values(self):
       res = super(activity_statement_config_setting, self).get_values()
       res.update({'automatic_statement': self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.automatic_statement'),
                   'send_to_options':self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.send_to_options'),
                   'statement_period':self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.statement_period'),
                   'mode': self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.mode'),
                   'test_email_address':self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.test_email_address'),
                   'cron_next_call_date': int(self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.cron_next_call_date'))})

       return res

    def set_values(self):
       res = super(activity_statement_config_setting, self).set_values()
       self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.automatic_statement',self.automatic_statement)
       self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.cron_next_call_date',self.cron_next_call_date)
       self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.send_to_options',self.send_to_options)
       self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.mode',self.mode)
       self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.test_email_address', self.test_email_address)
       self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.statement_period',self.statement_period)
       if self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.automatic_statement',self.automatic_statement):
           cron_id = self.env.ref('customer_activity_statement.partner_activity_statement_cron')
           cron_id.update({'nextcall': (cron_id.nextcall).replace(day=int(self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.cron_next_call_date',self.cron_next_call_date)))})
       return res

    @api.one
    @api.constrains('cron_next_call_date')
    def _check_cron_next_call_date(self):
        if self.automatic_statement and (self.cron_next_call_date < 1 or self.cron_next_call_date > 30):
            raise ValidationError(_('Please enter valid date.'))


class ResPartner(models.Model):
    _inherit = 'res.partner'

    statement_sent = fields.Boolean(string="Statement Sent")

    @api.multi
    def update_statement_sent(self):
        self.search([]).update({'statement_sent': False})
        # for each in partner_ids:
        #     each.statement_sent = False