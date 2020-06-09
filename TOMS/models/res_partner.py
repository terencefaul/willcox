from odoo import models, fields, api, _
from datetime import datetime, date
from ast import literal_eval
# from mock.mock import self
from odoo.exceptions import UserError, ValidationError,Warning
import re


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('company_type')
    def onchange_company_type(self):
        super(res_partner, self).onchange_company_type()
        if self.company_type == 'person' and not self.parent_id:
            self.medical_aid_id = self.env.ref("TOMS.medical_aid_private")
        else:
            self.medical_aid_id = False

    @api.onchange('medical_aid_id')
    def _onchange_medical_aid(self):
        if self.medical_aid_id.name == 'Private':
            self.property_payment_term_id = self.env.ref('account.account_payment_term_immediate').id
        else:
            self.property_payment_term_id = self.env.ref('account.account_payment_term_15days').id

    is_a_medical_aid = fields.Boolean(string="Is a Medical Aid")
    is_a_medical_aid_administrator = fields.Boolean(string="Is a Medical Aid Administrator")
    medical_aid_plan_ids = fields.One2many('medical.aid.plan', 'medical_aid_id', string="Plans")
    administrator_id = fields.Many2one('res.partner', string="Administrator")
    destination_code = fields.Char(string="Destination Code")
    msv_allowed = fields.Boolean(string="MSV Allowed")
    scr_allowed = fields.Boolean(string="SwitchClaim Reversal Allowed")
    st_allowed = fields.Boolean(string="Statistical Transactions Allowed")
    mpc_allowed = fields.Boolean(string="Member Paid Claims Allowed")
    era_active = fields.Boolean(string="eRA Active")
    ba_allowed = fields.Boolean(string="Benefit Availability Allowed")
    bc_allowed = fields.Boolean(string="Benefit Check Allowed")
    period_cycle = fields.Char(string="Period/Cycle")
    is_contracted = fields.Boolean(string="Contracted")
    admin_code = fields.Char(string="Admin Code")
    medical_aid_key = fields.Char(string="Medical Aid Key")
    patient_number = fields.Char(string="Patient Number")
    surname = fields.Char(string="Surname")
    medical_aid_id = fields.Many2one('res.partner', string="Medical Aid")
    option_id = fields.Many2one('medical.aid.plan', string="Plan")
    plan_option_id = fields.Many2one('medical.aid.plan.option', string="Option", domain="[('plan_id','=',option_id)]")
    medical_aid_no = fields.Char(string="Medical Aid No")
    dependent_code = fields.Char(string="Dependent Code", size=3)
    initials = fields.Char(string="Initials")
    first_name = fields.Char(string="First Name")
    nick_name = fields.Char(string="Nickname")
    id_number = fields.Char(string="ID Number", size=13 )
    birth_date = fields.Date(string="Birthday")
    gender = fields.Selection([('m', 'Male'), ('f', 'Female')], string="Gender")
    employer = fields.Char(string="Employer")
    occupation = fields.Many2one('customer.occupation', string='Occupation')
    function = fields.Many2one('customer.function', string="Job Description")
    communication = fields.Selection([('cell_phone', 'Cell Phone'),
                                      ('email', 'Email'),
                                      ('fax', 'Fax'),
                                      ('post', 'Post'),
                                      ('telephone_home', 'Telephone - Home'),
                                      ('telephone_work', 'Telephone - Work'),
                                      ])
    file_no = fields.Integer(string="File No")
    old_system_no = fields.Char(string="Old System No")
    work_address = fields.Char(string="Work Address")
    work_phone = fields.Char(string="Work Phone")
    # source_ids = fields.Many2many('customer.source', string="Source")
    source_id = fields.Many2one('customer.source', string="Source")
    individual_internal_ref = fields.Char(string="")
    home_street = fields.Char(string="")
    home_street2 = fields.Char(string="")
    home_city = fields.Char(string="")
    home_state_id = fields.Many2one('res.country.state', string="")
    home_zip = fields.Char(string="")
    home_country_id = fields.Many2one('res.country', string="")
    work_street = fields.Char(string="")
    work_street2 = fields.Char(string="")
    work_city = fields.Char(string="")
    work_state_id = fields.Many2one('res.country.state', string="")
    work_zip = fields.Char(string="")
    work_country_id = fields.Many2one('res.country', string="")
    is_key_member = fields.Boolean(string="Is Key Member")
    is_dependent = fields.Boolean(string="Is Dependent")
    contact_type = fields.Selection([('contact', 'Contact')], default="contact")
    msv_later_button = fields.Boolean(string="MSV Later")
    msv_partner_id = fields.Many2one('res.partner',string="Msv's Partner")
    msv_latest_date = fields.Datetime(string="Latest Msv Date")
    msv_status = fields.Text(string="MSV Status")
    sport = fields.Many2many('hway.sport', string="Do You Play Sport")
    hobby = fields.Many2many('hway.hobby', string="Do You have a hobby")
    doyou = fields.Many2many('hway.doyou', string="Do You")
    doesyour = fields.Many2many('hway.doesyour', string="Does your")
    customer_language = fields.Many2one('customer.language',string='Patient Language')

    @api.model
    def create(self, vals):
        self = self.with_context(key='from_create')
        if vals.get('customer') and vals.get('company_type') == 'person':
            vals.update({'name': vals.get('first_name', '') + ' ' + vals.get('surname', '')})
        if vals.get('email'):
            if not re.search(r'\w+@\w+', vals.get('email')):
                raise ValidationError(_("Invalid Email Address"))
        res = super(res_partner, self).create(vals)
        # res.copy_postal_address_to_home_add()
        if res.company_type == 'person':
            if res.parent_id:
                if not res.parent_id.individual_internal_ref:
                    if res.parent_id.customer:
                        res.parent_id.individual_internal_ref = self.env['ir.sequence'].next_by_code('res.partner')
                        res.parent_id.file_no = self.env['ir.sequence'].next_by_code('file_no')
                        res.parent_id.patient_number = 'SWHFO-' + res.parent_id.individual_internal_ref.split('-')[
                            1] + "-" + "0"
                        res.parent_id.is_key_member = True
                partner_ids = res.parent_id.child_ids.filtered(lambda l: l.type == 'contact')
                if res.parent_id.customer:
                    if partner_ids:
                        patient_num = int(res.parent_id.patient_number.split('-')[1]) + 1
                        partner_ids.write({'individual_internal_ref': res.parent_id.individual_internal_ref,
                                           'customer': res.parent_id.customer,
                                           'is_dependent': True,
                                           'medical_aid_id': res.parent_id.medical_aid_id.id,
                                           'option_id': res.parent_id.option_id.id,
                                           'phone': res.phone if res.phone else res.parent_id.phone,
                                           })
                        rec_id = self.search([('parent_id', '=', res.parent_id.id), ('id', '!=', res.id)],
                                             order="id desc", limit=1)
                        res.file_no = self.env['ir.sequence'].next_by_code('file_no')
                        if rec_id.patient_number:
                            cnt = int(rec_id.patient_number.split('-')[2]) + 1
                            res.patient_number = rec_id.patient_number.split('-')[0] + '-' + \
                                                 rec_id.patient_number.split('-')[1] + '-' + str(cnt)
                        else:
                            cnt = int(res.parent_id.patient_number.split('-')[2]) + 1
                            res.patient_number = res.parent_id.patient_number.split('-')[0] + '-' + \
                                                 res.parent_id.patient_number.split('-')[1] + '-' + str(cnt)
            else:
                if not res.individual_internal_ref:
                    if res.customer:
                        res.individual_internal_ref = self.env['ir.sequence'].next_by_code('res.partner')
                        res.file_no = self.env['ir.sequence'].next_by_code('file_no')
                        res.patient_number = 'SWHFO-' + res.individual_internal_ref.split('-')[1] + "-" + "0"
                        res.is_key_member = True
            res.ref = res.patient_number
        return res

    @api.multi
    def write(self, vals):
        first_name = vals.get('first_name', '')
        surname = vals.get('surname', '')
        if first_name and surname:
            vals['name'] = ''
            if first_name:
                vals['name'] += (first_name)
            if surname:
                vals['name'] += ' ' + (surname)
        if first_name and not surname:
            vals['name'] = ''
            if first_name:
                vals['name'] += (first_name)
                vals['name'] += ' ' + (self.surname)
        if surname and not first_name:
            vals['name'] = ''
            if surname:
                vals['name'] += (self.first_name)
                vals['name'] += ' ' + (surname)
        res = super(res_partner, self).write(vals)
        if not self._context.get('key'):
            for each in self.child_ids:
                each.write({
                    'option_id': vals.get('option_id') or self.option_id.id,
                    'phone': vals.get('phone') or self.phone,
                    'medical_aid_id': vals.get('medical_aid_id') or self.medical_aid_id.id
                })
        if vals.get('email'):
            if not re.search(r'\w+@\w+', vals.get('email')):
                raise ValidationError(_("Invalid Email Address"))
        return res

    @api.model
    def default_get(self, fields):
        rec = super(res_partner, self).default_get(fields)
        rec.update(
            country_id=self.env.ref('base.za').id
        )
        return rec

    @api.multi
    def res_partner_company_form(self):
        return {
            'name': 'Create Contact',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_id': self.env.ref('TOMS.aspl_res_partner_company_form').id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_parent_id': self.id, 'default_company_type': 'company'}
        }

    @api.multi
    def res_partner_child_form(self):
        return {
            'name': 'Create Contact',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_id': self.env.ref('TOMS.view_partner_dependent_contact_form').id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parent_id': self.id,
                'default_medical_aid_id': self.medical_aid_id.id,
                'default_option_id': self.option_id.id,
                'default_plan_option_id': self.plan_option_id.id,
                'default_home_street': self.home_street,
                'default_home_street2': self.home_street2,
                'default_home_city': self.home_city,
                'default_home_zip': self.home_zip,
                'default_home_state_id': self.home_state_id.id,
                'default_home_country_id': self.home_country_id.id,
                'default_is_dependent': True,
                'default_individual_internal_ref': self.individual_internal_ref,
                'default_country_id': self.env.ref('base.za').id,
                'default_medical_aid_no': self.medical_aid_no,
            }
        }

    @api.multi
    def save_child_contact(self):
        pass

    @api.multi
    def res_compnay_contact(self):
        pass

    @api.multi
    def save_medical_aid(self):
        pass

    @api.multi
    def copy_postal_address_to_home_add(self):
        self.home_street = self.street
        self.home_street2 = self.street2
        self.home_city = self.city
        self.home_state_id = self.state_id.id
        self.home_zip = self.zip
        self.home_country_id = self.country_id.id

    @api.multi
    @api.onchange('id_number')
    def compute_birthdate(self):
        self.birth_date = False
        if self.id_number:
            if len(self.id_number) == 13:
                if (int(self.id_number[2:4]) <= 12 and int(self.id_number[4:6]) <= 31):
                    curr_year = str(date.today().year)[2:4]
                    year = 19 if int(self.id_number[0:2]) > int(curr_year) else 20
                    birth_date = self.id_number[2:4] + '/' + self.id_number[4:6] + '/' + str(year) + self.id_number[0:2]
                    birth_date = datetime.strptime(birth_date, '%m/%d/%Y').date()
                    self.birth_date = birth_date

    @api.constrains('id_number')
    def check_duplicate_idnumber(self):
        if self.id_number:
            idnumber = self.env['res.partner'].search([('id_number', '=', self.id_number),('id','!=',self.id)])
            if idnumber:
                raise Warning(_('Duplicate ID Number Found.!!!'))

    @api.multi
    @api.onchange('first_name', 'surname')
    def onchange_first_name(self):
        self.name = False
        name = self.first_name if self.first_name else ''
        sname = self.surname if self.surname else ''
        name = name + ' ' + sname
        self.name = name.strip()

class customer_language(models.Model):
    _name = 'customer.language'
    _description = 'Preferred Language of customer'

    name = fields.Char()

class customer_occupation(models.Model):
    _name = 'customer.occupation'
    _description = 'Preferred occupation of customer'

    name = fields.Char()



class customer_source(models.Model):
    _name = 'customer.source'
    _description = 'Customer Source'

    name = fields.Char(string="Source")

class customer_funtion(models.Model):
    _name = 'customer.function'
    _description = 'Customer Function'

    name = fields.Char(string="Job Position")


class inherit_res_partner(models.Model):
    _inherit = 'res.partner'

    last_exam_date = fields.Date(string="Last Exam Date")
    recall_exam_date = fields.Date(string="Recall Date")

    @api.model
    def scheduler_recall_customer(self):
        customer_id = self.search([('customer', '=', True), ('recall_exam_date', '=', date.today())])
        sms_template_id = self.env.ref('TOMS.recall_sms_template')
        if sms_template_id:
            for each in customer_id:
                if each.mobile:
                    sms_compose = self.env['sms.compose'].create({
                        'sms_template_id': sms_template_id.id,
                        'from_mobile_id': sms_template_id.from_mobile_verified_id.id,
                        'to_number': each.mobile,
                        'sms_content': sms_template_id.template_body,
                        'media_id': sms_template_id.media_id,
                        'model': self._name,
                        'record_id': each.id
                    })
                    if sms_compose:
                        sms_compose.send_entity()



