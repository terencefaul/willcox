from odoo import models, api, fields, _
from datetime import datetime,date
from ast import literal_eval
import xml.etree.ElementTree as ET
from odoo.exceptions import UserError, ValidationError, Warning
import requests

class ResPartner(models.Model):
    _inherit = "res.partner"

    payload_description = fields.Text()


    @api.multi
    def submit_msv(self):
        current_date_time = datetime.now().strftime("%Y%m%d%H%M")
        ir_config_obj = self.env['ir.config_parameter']
        practice_number = ir_config_obj.sudo().get_param('mediswitch_integration.practice_number')
        practice_name = ir_config_obj.sudo().get_param('mediswitch_integration.practice_name')
        for partner in self:
            if not partner.medical_aid_id.msv_allowed:
                raise Warning(_('Sorry, MSV is not enabled for the patients Medical Aid.'))
            if not partner.surname:
                raise MissingError("Member Surname is missing")
            if not partner.name:
                raise MissingError("Member Name is missing")
            if not partner.individual_internal_ref:
                raise MissingError("Member Internal Ref is missing")
            birthday = partner.birth_date and partner.birth_date.strftime("%Y%m%d")
            if partner.gender:
                gender = partner.gender.upper()
            else:
                raise MissingError("Gender is missing")
            paylod = """H|%s|%s|%s|
S|%s|%s|%s|%s|
M|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|
E|%s|%s|\n""" % (
                #P|%s|%s|%s|%s|%s|%s|%s|%s|
                # Header (Start of Message) Record – Type ‘H’
                partner.id or '', 121, 'TOMS:2',
                # Service Provider Record – Type ‘S’
                current_date_time, practice_number or '', practice_name or '', '',
                # Member Record – Type ‘M’
                '1','',
                partner.title.name or 'N',
                partner.initials or 'N',
                partner.surname or '',
                partner.name or '', partner.medical_aid_no or '', 'N','',
                partner.medical_aid_id.destination_code or '',
                # Patient Record – Type ‘P’
                # partner.dependent_code or '', partner.surname or '',
                # partner.initials or '',
                # partner.name or '', birthday or '',
                # gender or '', '',
                # partner.id_number or '',
                # Footer Record – Type ‘E’
                partner.id or '', '1',
            )
            partner.write({'payload_description':paylod})
            if self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.for_what') == 'test':
                username = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.user_name_test')
                password = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.password_test')
                package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_test')
                mode = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.mode_test')
                txversion = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.txversion_test')
                url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.test_url')
            else:
                username = self.env['ir.config_parameter'].sudo().get_param(
                    'mediswitch_integration.user_name_production')
                password = self.env['ir.config_parameter'].sudo().get_param(
                    'mediswitch_integration.password_production')
                package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_production')
                mode = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.mode_production')
                txversion = self.env['ir.config_parameter'].sudo().get_param(
                    'mediswitch_integration.txversion_production')
                url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.production_url')
            xml1 = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v2="http://gateway.switchonline.co.za/MediswitchGateway/v2">
                           <soapenv:Header/>
                           <soapenv:Body>
                              <v2:submitOperation>
                                 <user>%s</user>
                                 <passwd>%s</passwd>
                                 <package>%s</package>
                                 <destination>%s</destination>
                                 <txType>301</txType>
                                 <mode>%s</mode>
                                 <txVersion>%s</txVersion>
                                 <userRef>%s</userRef>
                                 <payload>%s</payload>
                              </v2:submitOperation>
                           </soapenv:Body>
                        </soapenv:Envelope>
                        """ % (
                username, password, package, partner.plan_option_id.destination_code,mode,
                txversion,
                partner.id, paylod)
            try:
                headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
                response = requests.post(url, headers=headers, data=xml1.encode('utf-8'))
                response_string = ET.fromstring(response.content)
            except Exception as e:
                raise Warning(_('502 Bad Gateway'))
            responsepayload = False
            list1 = []
            wizard_data = {'partner_id': partner.id, 'msv_type': 'msv', 'request_payload': paylod}
            for node in response_string.iter():
                if node.tag == 'responsePayload':
                    responsepayload = node.text
            if responsepayload:
                wizard_data.update({"response_payload": responsepayload})
                lines = responsepayload.split("\n")
                strings = ("Invalid Missing", "Invalid")
                if any(s in lines[0] for s in strings):
                    raise Warning(_(lines[0]))
                if lines and lines[0] and lines[0].startswith('H'):
                    for line in lines:
                        if line.startswith('RV'):
                            split_line = line.split("|")
                            if split_line[1] == '01':
                                raise Warning(_(split_line[5]))
                if lines and lines[0] and lines[0].startswith('H'):
                    for line in lines:
                        effective_date = False
                        termination_date = False
                        if line.startswith('P'):
                            split_line = line.split("|")
                            partner.msv_status = split_line[10]
                            if split_line[5]:
                                dob= date(year=int(split_line[5][0:4]), month=int(split_line[5][4:6]), day=int(split_line[5][6:9]))
                            if split_line[8]:
                                effective_date = date(year=int(split_line[8][0:4]), month=int(split_line[8][4:6]),
                                                      day=int(split_line[8][6:9]))
                            if split_line[9]:
                                termination_date = date(year=int(split_line[9][0:4]), month=int(split_line[9][4:6]),
                                                        day=int(split_line[9][6:9]))
                            list1.append({
                                'name': split_line[4] or False,
                                'surname': split_line[2] or False,
                                'dependent_code': split_line[1] or False,
                                'initials': split_line[3] or False,
                                'dob': dob or False,
                                'id_number': split_line[6] or False,
                                'gender': split_line[7] or False,
                                'effective_date': effective_date,
                                'termination_date': termination_date,
                                'status_code_description': split_line[10] or False,
                            })
                        if line.startswith('M'):
                            split_line = line.split("|")
                            wizard_data.update({
                                'membership_number':split_line[4],
                                'medical_scheme_name': split_line[12],
                                'plan_name':split_line[15],
                                'option_name':split_line[15]
                            })
                        if line.startswith('RV'):
                            split_line = line.split("|")
                            if split_line[6] and split_line[6] == '01':
                                validation_code = '01 - CDV (Check Digit Verification)'
                            elif split_line[6] and split_line[6] == '02':
                                validation_code = '02 - CHF (Card Holder File)'
                            elif split_line[6] and split_line[6] == '03':
                                validation_code = '03 - SO (Switch out to Medical Scheme)'
                            wizard_data.update({
                                'validation_code':validation_code or False,
                                'disclaimer': split_line[3] or False,
                                'status_code_description' : split_line[5] or False,
                            })
            partner.msv_later_button = False
            wizard_id = self.env['msv.response'].create(wizard_data)
            if list1:
                for data in list1:
                    data.update({'msv_response_id': wizard_id.id})
                    self.env['msv.members'].create(data)
            partner.msv_latest_date = wizard_id.create_date
            return {
                'name': 'Msv Response Wizard',
                'type': 'ir.actions.act_window',
                'res_model': 'msv.response',
                'res_id': wizard_id.id,
                'view_id': self.env.ref('mediswitch_integration.form_view_for_msv_response1').id,
                'view_mode': 'form',
                'target': 'new',
            }

    @api.multi
    def action_view_partner_msv(self):
        self.ensure_one()
        action = self.env.ref('mediswitch_integration.action_partner_msv1').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        return action

class MsvResponse(models.Model):
    _name = "msv.response"
    _description = "Response from MSV to Mediswitch"
    _order = 'create_date desc'
    #Member Details
    msv_type = fields.Selection([('msv', 'Msv'), ('id_msv', 'Id Msv'), ('sur_dob_msv', 'Surname Dob Msv')], string="Msv Type")
    partner_id = fields.Many2one("res.partner")
    membership_number = fields.Char(string="Membership Number")
    name = fields.Char(string="Medical Aid")
    plan_name = fields.Char(string="Plan")
    option_name = fields.Char(string="Option")
    # Response Details
    status_code_description = fields.Char(string="Result Description", help="Patient’s Medical Scheme Status Code and Description")
    validation_code = fields.Char(string="Validation Method Indicator")
    disclaimer = fields.Char(string="Disclaimer")
    request_payload = fields.Text()
    response_payload = fields.Text()
    msv_members_ids = fields.One2many("msv.members",'msv_response_id')


