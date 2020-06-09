# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime,date
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
import logging
import calendar
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
_logger = logging.getLogger(__name__)


class CustomerActivityStatementWizard(models.TransientModel):
    """Customer Activity Statement wizard."""

    _name = 'customer.activity.statement.wizard'
    _description = 'Customer Activity Statement Wizard'

    @api.model
    def get_fiscal_date(self):
        company_fiscalyear_dates = self.env.user.company_id.compute_fiscalyear_dates(datetime.now())
        dt_from = company_fiscalyear_dates['date_from'] if company_fiscalyear_dates['date_from'] else fields.Date.to_string(
                                 date(date.today().year, 1, 1))
        dt_to = company_fiscalyear_dates['date_to'] if company_fiscalyear_dates['date_to'] else fields.Date.to_string(date.today())
        return [dt_from.date(), dt_to.date()]

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    date_start = fields.Date(required=True,
                             default=lambda self:self.get_fiscal_date()[0])
    date_end = fields.Date(default=date.today())
    show_aging_buckets = fields.Boolean(string='Include Aging Buckets',
                                        default=True)
    number_partner_ids = fields.Integer(
        default=lambda self: len(self._context['active_ids'])
    )
    filter_partners_non_due = fields.Boolean(
        string='Don\'t show partners with no due entries', default=True)
    account_type = fields.Selection(
        [('receivable', 'Receivable'),
         ('payable', 'Payable')], string='Account type', default='receivable')

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        return self._export()

    def _prepare_activity_statement(self):
        self.ensure_one()
        data__prepare_activity_statement =  {
            'date_start': self.date_start,
            'date_end': self.date_end,
            'company_id': self.company_id.id,
            'partner_ids': self._context['active_ids'] if self._context.get('active_ids') else [self._context.get('params').get('id')],
            'show_aging_buckets': self.show_aging_buckets,
            'filter_non_due_partners': self.filter_partners_non_due,
            'account_type': self.account_type,
        }
#          if self._context.get('active_ids') else [self._context.get('params').get('id')]
        return data__prepare_activity_statement

    def _export(self):
        """Export to PDF."""
        data = self._prepare_activity_statement()
        report_id = self.env.ref(
            'customer_activity_statement'
            '.action_print_customer_activity_statement').report_action(
            self, data=data)
        return self.env.ref(
            'customer_activity_statement'
            '.action_print_customer_activity_statement').report_action(
            self, data=data)

    @api.multi
    def sent_activity_statement_by_email(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('customer_activity_statement', 'email_template_partner_statement')[1]
        except ValueError:
            template_id = False
        if template_id:
            try:
                body_html = """
                                <p>Dear Sir/Madam,</p>
                                <p>Please find attached your account statement. If you have any queries, please feel free to contact us.</p>
                                <br/>
                                <p>Regards,<p/>
                              """
                body_html += """<p>""" + self.company_id.name + """</p>"""
                template_obj = self.env['mail.template'].browse(template_id)
                for each in self._context.get('active_ids'):
                    partner_id = self.env['res.partner'].browse(each)
                    template_obj.email_to = partner_id.email
                    template_obj.subject = partner_id.company_id.name + ' Customer Statement' + ' (' + (partner_id.ref if partner_id.ref else '') + ')'
                    template_obj.body_html = body_html,
                    template_obj.report_name = "Statement "+ str(date.today())
                    record_id = template_obj.with_context(partner_ids=[each]).send_mail(self.id, force_send=True, raise_exception=True)
                    # template_obj.with_context(partner_ids=[each]).send_mail(self.id)
                    mail_id = self.env['mail.mail'].browse(record_id)
                    mail_id.write({
                                    'res_id':partner_id.id,
                                    'model':'res.partner'
                                    })
            except Exception as e:
                _logger.error('Unable to send email for order %s',e)

    @api.model
    def sent_activity_statement_by_email_cron(self):
        config_id = self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.cron_next_call_date')
        if int(config_id) == datetime.now().day:
            automatic_statement = self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.automatic_statement')
            if config_id and automatic_statement:
                # cron_next_call_date = int(self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.cron_next_call_date'))
                ir_model_data = self.env['ir.model.data']
                try:
                    template_id = ir_model_data.get_object_reference('customer_activity_statement', 'email_template_partner_statement')[1]
                except ValueError:
                    template_id = False
                if template_id:
                    # try:
                    template_obj = self.env['mail.template'].browse(template_id)
                    partner_list = []
                    if self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.send_to_options') == 'outstanding_balance_only':
                        partner_list.append([x.id for x in self.env['res.partner'].search([('statement_sent','=',False)]).filtered(lambda l:(l.credit - l.debit) != 0)])
                    else:
                        partner_list.append([x.id for x in self.env['res.partner'].search([('statement_sent','=',False)])])
                    partner_list = [partner_list[0][:200]]

                    wiz_id = self.create({'number_partner_ids': len(partner_list)})
                    date  = datetime.now()
                    if self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.statement_period') == 'current_month':
                        wiz_id.write({
                                      'date_start' : date.replace(day = 1),
                                      'date_end' : date.today(),
                                      })
                    if self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.statement_period') == 'current_quarter':
                        start_date = wiz_id.date_start
                        end_date = wiz_id.date_start + relativedelta(months=3,days=-1)
                        count = 1
                        today_date = datetime.now().date()
                        start_date = wiz_id.date_start
                        end_date = wiz_id.date_start + relativedelta(months= 3*count,days=-1)
                        for each in range(1,5):
                            if today_date > start_date and today_date < end_date:
                                wiz_id.write({
                                              'date_start' : start_date,
                                              'date_end' : date.today()
                                              })
                            else:
                                count = count + 1
                                start_date = end_date + relativedelta(days=1)
                                end_date = datetime.strptime(str(wiz_id.date_start), DF).date() + relativedelta(months= 3*count,days=-1)
                    if partner_list:
                        for each in partner_list[0]:
                            partner_id = self.env['res.partner'].browse(each)
                            wiz_id.account_type = 'payable' if (not partner_id.customer and partner_id.supplier) else 'receivable'
                            template_obj.email_to = partner_id.email
                            template_obj.subject = partner_id.company_id.name + ' Customer Statement' + ' (' + (partner_id.ref if partner_id.ref else '') + ')'
                            template_obj.report_name = "Statement "+ str(date.today())
                            if self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.mode') == "Test":
                                test_email_address = self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.test_email_address')
                                template_obj.email_to = test_email_address
                                record_id = template_obj.with_context(partner_ids=[each]).send_mail(wiz_id.id, force_send=True, raise_exception=True)
                            if self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.mode') == "Production":
                                # template_obj.send_mail(wiz_id.id,force_send=True, raise_exception=True)

                                record_id = template_obj.with_context(partner_ids=[each]).send_mail(wiz_id.id,force_send=True, raise_exception=True)
                            mail_id = self.env['mail.mail'].browse(record_id)
                            mail_id.write({
                                            'model':'res.partner',
                                            'res_id':partner_id.id
                                            })
                            partner_id.statement_sent = True

                    # except Exception as e:
                    #     _logger.error('Unable to send email for order %s',e)
            # cron_id = self.env.ref('customer_activity_statement.partner_activity_statement_cron')
            # cron_id.update({'nextcall': fields.Date.from_string(cron_id.nextcall).replace(day=cron_next_call_date)})