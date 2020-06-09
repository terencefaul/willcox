from odoo import fields, models, api, _
from suds.wsse import Security, UsernameToken
from suds.client import Client
from datetime import datetime
from odoo.http import request
from datetime import date
from odoo.exceptions import MissingError
import xml.etree.ElementTree as ET
import time
import json
import requests

from odoo.exceptions import UserError, ValidationError, Warning

STATE_SELECTION = [
        ('01', 'Accepted for delivery'),
        ('02', 'Accepted for processing'),
        ('03', 'Rejected'),
        ('04', 'Approved for Payment'),
        ('05', 'Approved for Part Payment'),
        ('06', 'Reversal Accepted'),
        ('07', 'Reversal Rejected'),
]

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    medical_aid_pay = fields.Boolean(string="Medical Aid Pay", default=True)
    date_invoice = fields.Date(string="Invoice Date", default=datetime.today().date())
    medical_aid_claims_lines = fields.One2many("mediswitch.submit.claim", "invoice_id")
    status_claim = fields.Char(string="Claim Status", invisible="1")
    claim_level_mediswitch_status = fields.Selection(STATE_SELECTION, string="Claim Level Status", track_visibility='onchange')
    user_ref = fields.Char()

    @api.onchange('payment_term_id')
    def check_payment_term(self):
        medical_aid_ref = self.env.ref('account.account_payment_term_15days').id
        if self.payment_term_id.id == medical_aid_ref:
            self.medical_aid_pay = True
        else:
            self.medical_aid_pay = False



    @api.multi
    def action_submit_claim(self):
        current_date_time = datetime.now().strftime("%Y%m%d%H%M")
        ir_config_obj = self.env['ir.config_parameter']
        practice_number = ir_config_obj.sudo().get_param('mediswitch_integration.practice_number')
        practice_name = ir_config_obj.sudo().get_param('mediswitch_integration.practice_name')
        for invoice in self:
            if not invoice.partner_id.surname:
                raise MissingError("Member Surname is missing")
            if not invoice.partner_id.name:
                raise MissingError("Member Name is missing")
            if not invoice.partner_id.individual_internal_ref:
                raise MissingError("Member Internal Ref is missing")
            if not invoice.patient_id.surname:
                raise MissingError("Patient Surname is missing")
            if not invoice.patient_id.name:
                raise MissingError("Patient Name is missing")
            if not invoice.optometrist_id.op_number:
                raise MissingError("Doctor PCNS number is missing")
            birthday = invoice.patient_id.birth_date and invoice.patient_id.birth_date.strftime("%Y%m%d")
            recall_exam_date = invoice.patient_id.recall_exam_date and invoice.patient_id.recall_exam_date.strftime(
                "%Y%m%d")
            invoice_date = invoice.date_invoice and invoice.date_invoice.strftime(
                "%Y%m%d")
            if invoice.patient_id.dependent_code and len(invoice.patient_id.dependent_code) > 12:
                p2_val = invoice.patient_id.dependent_code[0:12]
            else:
                p2_val = invoice.patient_id.dependent_code
            if invoice.partner_id.name and len(invoice.partner_id.name) > 30:
                m6_val =invoice.partner_id.name[0:30]
            else:
                m6_val = invoice.partner_id.name
            if invoice.partner_id.medical_aid_id.name and len(invoice.partner_id.medical_aid_id.name) > 20:
                m17_val =invoice.partner_id.medical_aid_id.name[0:20]
            else:
                m17_val = invoice.partner_id.medical_aid_id.name
            new_individual_internal_ref = ''
            if invoice.partner_id and invoice.partner_id.individual_internal_ref and '-' in invoice.partner_id.individual_internal_ref:
                new_individual_internal_ref = invoice.partner_id.individual_internal_ref.replace('-', '')
            paylod = """H|%s|%s|%s|%s|
S|%s|%s|%s|%s|%s|
M|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|
P|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n""" % (
                # Header (Start of Message) Record – Type ‘H’
                invoice.id or '', 120, 'TOMS2', '',
                # Service Provider Record – Type ‘S’
                current_date_time, practice_number or '', practice_name or '', '',
                self.env.user.company_id.vat or '',
                # Member Record – Type ‘M’
                invoice.partner_id.id_number or '', invoice.partner_id.title.shortcut or '',
                invoice.partner_id.initials or 'N',
                invoice.partner_id.surname or '',
                m6_val or '', invoice.partner_id.medical_aid_no or '', 'N',
                new_individual_internal_ref,
                invoice.partner_id.street or '', invoice.partner_id.street2 or '', invoice.partner_id.city or '',
                invoice.partner_id.zip or '',
                invoice.partner_id.mobile or '', invoice.partner_id.option_id.name or '', '',
                m17_val or '', invoice.partner_id.medical_aid_id.ref or '', '03',
                'network',
                invoice.partner_id.medical_aid_id.destination_code or '',
                # Patient Record – Type ‘P’
                p2_val or '', invoice.patient_id.surname or '',
                invoice.patient_id.initials or '',
                invoice.patient_id.name or '', birthday or '',
                invoice.patient_id.gender and invoice.patient_id.gender.upper() or '', '',
                invoice.patient_id.id_number or '', recall_exam_date or '', '', '', '', '', '', '', '', '',
                '', '01', '', '', invoice.id or '',
            )
            count = 1
            # wdb.set_trace()
            for line in invoice.invoice_line_ids:
                if not line.product_id.default_code:
                    raise MissingError("Tariff Code/Ref is missing")
                # T
                paylod += """T|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n""" % (
                    # Treatment Record – Type ‘T’
                    count, invoice_date, invoice_date, '', invoice.id or '',
                    line.id, '02',
                    int(line.quantity * 100 or 0), '06', line.product_id.default_code or '', '05', '',
                    '', '10',
                    line.product_id.name or '',
                    '',
                    '', '', '',
                    '', '', '', '', '', '', '11')
                # OP records
                if line.final_rx_id:
                    rx_data = line.final_rx_id

                    # Left side values
                    op_count = 1
                    L_v12_val = ''
                    L_v13_val = ''
                    if rx_data.od_prism:
                        L_v12_val = int(str(rx_data.od_prism)[0]) * 100
                        if len(rx_data.od_prism) > 1:
                            L_v13_val = rx_data.od_prism[1:]
                    if line.product_id.name and len(line.product_id.name) > 50:
                        v4_val = line.product_id.name[0:51]
                    else:
                        v4_val = line.product_id.name
                    # v12_val = rx_data.od_prism.isdigit()
                    paylod += """OP|{v2}|{v3}|{v4}|{v5}|{v6}|{v7}|{v8}|{v9}|{v10}|{v11}|{v12}|{v13}|{v14}|{v15}|\n""".format(
                        # OP Record – Type ‘OP’
                        v2=op_count,
                        v3=line.product_id.seller_ids and line.product_id.seller_ids[
                            0].display_name or "None Specified",
                        v4=v4_val or '',
                        v5='',
                        v6='',
                        v7='L',
                        v8=int(rx_data.od_syh * 100) or '',
                        v9=int(rx_data.od_cyl * 100) or '',
                        v10=int(rx_data.od_axis * 100) or '',
                        v11=int(rx_data.od_add * 100) or '',
                        v12=L_v12_val,
                        v13=L_v13_val, v14='',
                        v15=line.product_id.name or '',
                    )

                    # Right_side_values
                    op_count += 1
                    R_v12_val = ''
                    R_v13_val = ''
                    if rx_data.os_prism:
                        R_v12_val = int(rx_data.os_prism[0]) * 100
                        if len(rx_data.os_prism) > 1:
                            R_v13_val = rx_data.os_prism[1:]
                    paylod += """OP|{v2}|{v3}|{v4}|{v5}|{v6}|{v7}|{v8}|{v9}|{v10}|{v11}|{v12}|{v13}|{v14}|{v15}|\n""".format(
                        # OP Record – Type ‘OP’
                        v2=op_count,
                        v3=line.product_id.seller_ids and line.product_id.seller_ids[
                            0].display_name or "None Specified",
                        v4=v4_val or '',
                        v5='',
                        v6='',
                        v7='R',
                        v8=int(rx_data.os_syh * 100) or '',
                        v9=int(rx_data.os_cyl * 100) or '',
                        v10=int(rx_data.os_axis * 100) or '',
                        v11=int(rx_data.os_add * 100) or '',
                        v12=R_v12_val,
                        v13=R_v13_val, v14='',
                        v15=line.product_id.name or '',
                    )
                # DR
                # print("\n\n\n\n")
                paylod += """DR|%s|%s|%s|%s|%s|%s|%s|%s|\n""" % (
                    practice_number or '', practice_name or '', '01',
                    invoice.optometrist_id.op_number or '', '01', '', '', '',
                )
                d_count = 1

                for each in line.icd_codes_ids:
                    paylod += """D|%s|%s|%s|%s|%s|\n""" % (  # D
                        '01', '01', each.code, '', '01' if d_count == 1 else '02',)
                    d_count += 1
                paylod += """Z|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n""" % (
                    # Treatment Financial Record – Type ‘Z’
                    int(line.price_total * 100),
                    int(line.price_total * 100), '', '', '', '', '', '', '',
                    int(line.price_total * 100), '', '', '', '', '',
                    int(line.price_total * 100), '',
                )
                count += 1
            paylod += """F|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|
E|%s|%s|%s|\n""" % (
                # Claim Financial Record – Type ‘F’
                int(invoice.amount_total * 100), int(invoice.amount_total * 100), int(invoice.amount_total * 100),
                '', '', '', '',
                invoice.id or '',
                '', int(invoice.amount_total * 100), '',
                # Footer (End of Message) Record – Type ‘E’
                invoice.id or '', '1', int(invoice.amount_total * 100),
            )
            invoice.write({'comment': paylod.strip()})
            if self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.for_what') == 'test':
                username = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.user_name_test')
                password = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.password_test')
                package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_test')
                txtype = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.txtype_test')
                mode = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.mode_test')
                txversion = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.txversion_test')
                url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.test_url')
            else:
                username = self.env['ir.config_parameter'].sudo().get_param(
                    'mediswitch_integration.user_name_production')
                password = self.env['ir.config_parameter'].sudo().get_param(
                    'mediswitch_integration.password_production')
                package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_production')
                txtype = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.txtype_production')
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
                     <txType>%s</txType>
                     <mode>%s</mode>
                     <txVersion>%s</txVersion>
                     <userRef>%s</userRef>
                     <payload>%s</payload>
                  </v2:submitOperation>
               </soapenv:Body>
            </soapenv:Envelope>
            """ % (
                username, password, package, invoice.partner_id.plan_option_id.destination_code, txtype, mode,
                txversion,
                invoice.id, paylod)
            headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
            response = requests.post(url, headers=headers, data=xml1.encode('utf-8'))
            response_string = ET.fromstring(response.content)
            data_dict = {}
            responsepayload = False
            for node in response_string.iter():
                if node.tag == 'swref':
                    invoice.user_ref = node.text
                    data_dict.update({'switch_reference': node.text})
                elif node.tag == 'responsePayload':
                    data_dict.update({'response_payload': node.text})
                    responsepayload = node.text
                elif node.tag == 'message':
                    raise Warning(_(node.text))
                else:
                    data_dict.update({str(node.tag): node.text})
            data_dict.update(
                {'invoice_id': self.id, 'destination_code': invoice.partner_id.plan_option_id.destination_code or '',
                 'user_reference': invoice.id or '', 'generated_payload': paylod,
                 'response_payload_date': datetime.now()})
            claim_id = self.env['mediswitch.submit.claim'].create(data_dict)
            if responsepayload:
                claim_status_lines = []
                order_lines = []
                lines = responsepayload.split("\n")
                strings = ("Invalid Missing", "Invalid")
                if any(s in lines[0] for s in strings):
                    raise Warning(_(lines[0]))
                if lines and lines[0] and lines[0].startswith('H'):
                    flag = 0
                    treatment_line = 0
                    balance_price = 0
                    approved_price = 0
                    total_approved_price = 0
                    rejection_count = ''
                    list1 = []
                    number = 0
                    message = ''
                    for line in lines:
                        split_line = line.split("|")
                        if line.startswith('S'):
                            if int(line.split("|")[5]) >= 0:
                                flag = 1
                        if line.startswith('R') and flag == 1:
                            rejection_count += "\n" + split_line[2] + ' - ' + split_line[1]
                        if line.startswith('FR') and flag == 1:
                            rejection_count += "\n" + split_line[1]
                        if line.startswith('G'):
                            rejection_count += "\n" + split_line[1]
                        if line.startswith('P') and flag == 1:
                            message11, message2, message3 = self.claim_messages(split_line[13], split_line[14],
                                                                                split_line[15])
                            message = message3 + ' - ' + message11 + ', from ' + message2 + '\n'
                            invoice.claim_level_mediswitch_status = split_line[13]
                        if line.startswith('T') and flag == 1:
                            treatment_line += 1
                            message1, message2, message3 = self.claim_messages(split_line[14], split_line[15],
                                                                               split_line[16])
                            claim_status_lines.append(message1)
                        if line.startswith('Z'):
                            if split_line[18]:
                                approved_price = int(split_line[18]) / 100
                                total_approved_price += approved_price
                            if split_line[16]:
                                balance_price = int(split_line[16]) / 100
                            list1.append({'approve': approved_price, 'balance': balance_price})
                        claim_id.response_error = rejection_count
                    if total_approved_price:
                        self.action_invoice_open()
                        vals = {}
                        accquire_id = self.env['payment.acquirer'].search([('name', '=', 'Mediswitch Payment Gateway')])
                        vals.update({
                            'amount': total_approved_price,
                            'currency_id': self.env.user.company_id.currency_id.id,
                            'partner_id': invoice.partner_id.id,
                            'invoice_ids': [(6, 0, invoice.ids)],
                            'state': 'done',
                        })
                        vals['acquirer_id'] = accquire_id.id
                        vals['reference'] = invoice.name
                        transaction = self.env['payment.transaction'].create(vals)
                        journal_id = request.env['account.journal'].sudo().search(
                            [('type', '=', 'bank')], limit=1)
                        payment_method_id = self.env['account.payment.method'].search(
                            [('name', '=', 'Manual'), ('payment_type', '=', 'outbound')], limit=1)
                        payments = {
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'partner_id': invoice.partner_id.id,
                            'amount': total_approved_price,
                            'journal_id': journal_id.id,
                            'payment_date': date.today(),
                            'communication': invoice.number,
                            'payment_method_id': payment_method_id.id,
                            'invoice_ids': [(4, invoice.id)],
                            'payment_transaction_id': transaction.id,
                        }
                        payment_id = self.env['account.payment'].create(payments)
                        payment_id.post()
                    for each in invoice.invoice_line_ids:
                        if len(claim_status_lines) > 0 and claim_status_lines[number]:
                            status = claim_status_lines[number]
                        else:
                            status = ""
                        each.approved_amount = list1[number].get('approve')
                        each.balance_amount = list1[number].get('balance')
                        each.claim_status = status
                        line = [0, 0, {'product_id': each.product_id.id,
                                       'quantity': each.quantity,
                                       'price_unit': each.price_unit,
                                       'approved_amount': list1[number].get('approve'),
                                       'balance_amount': list1[number].get('balance'),
                                       'tax_ids': [[4, id.id] for id in
                                                   each.invoice_line_tax_ids] if each.invoice_line_tax_ids else False,
                                       'price_subtotal': each.price_subtotal, 'status':status}]
                        order_lines.append(line)
                        number += 1

                    view_id = self.env['response.error.wizard'].sudo().create(
                        {'name': message, 'response_error': rejection_count or '', 'practise_name': practice_name,
                         'practise_number': practice_number, 'Medical_aid': invoice.partner_id.medical_aid_id.name,
                         'patient_name': invoice.patient_id.id, 'patient_dob': invoice.patient_id.birth_date,
                         'invoice_id': invoice.id or '', 'member_no': invoice.partner_id.medical_aid_no,
                         'claim_status_lines_ids': order_lines,
                         })
                    return {
                        'name': 'Response Wizard',
                        'type': 'ir.actions.act_window',
                        'res_model': 'response.error.wizard',
                        'res_id': view_id.id,
                        'view_id': self.env.ref('mediswitch_integration.response_error_wizard').id,
                        'view_mode': 'form',
                        'target': 'new',
                    }

    def claim_messages(self, no1, no2, no3):
        message_1 = ''
        message_2 = ''
        message_3 = ''
        if no1 and str(no1) in ['01', '02', '03', '04', '05', '06']:
            if str(no1) == '01':
                message_1 = 'Claim Accepted for delivery'
            elif str(no1) == '02':
                message_1 = 'Claim Accepted for processing'
            elif str(no1) == '03':
                message_1 = 'Claim Rejected'
            elif str(no1) == '04':
                message_1 = 'Claim Approved for Payment'
            elif str(no1) == '05':
                message_1 = 'Claim Approved for Part Payment'
            elif str(no1) == '06':
                message_1 = 'Claim Reversal Accepted'
            elif str(no1) == '07':
                message_1 = 'Claim Reversal Rejected'
        if no2 and str(no2) in ['01', '02']:
            if str(no2) == '01':
                message_2 = 'MediSwitch'
            elif str(no2) == '02':
                message_2 = 'Medical Scheme / Administrator'
        if no3 and str(no3) in ['01', '02', '03', '04']:
            if str(no3) == '01':
                message_3 = 'Real-Time'
            elif str(no3) == '02':
                message_3 = 'Batched'
            elif str(no3) == '03':
                message_3 = 'Queued'
            elif str(no3) == '04':
                message_3 = 'Rejected'
        return message_1, message_2, message_3

    @api.multi
    def action_reverse_claim(self):
        current_date_time = datetime.now().strftime("%Y%m%d%H%M")
        ir_config_obj = self.env['ir.config_parameter']
        practice_number = ir_config_obj.sudo().get_param('mediswitch_integration.practice_number')
        practice_name = ir_config_obj.sudo().get_param('mediswitch_integrat ion.practice_name')
        for invoice in self:
            if not invoice.partner_id.surname:
                raise MissingError("Member Surname is missing")
            if not invoice.partner_id.name:
                raise MissingError("Member Name is missing")
            if not invoice.partner_id.individual_internal_ref:
                raise MissingError("Member Internal Ref is missing")
            if not invoice.patient_id.surname:
                raise MissingError("Patient Surname is missing")
            if not invoice.patient_id.name:
                raise MissingError("Patient Name is missing")
            if not invoice.optometrist_id.op_number:
                raise MissingError("Doctor PCNS number is missing")
            birthday = invoice.patient_id.birth_date and invoice.patient_id.birth_date.strftime("%Y%m%d")
            recall_exam_date = invoice.patient_id.recall_exam_date and invoice.patient_id.recall_exam_date.strftime(
                "%Y%m%d")
            invoice_date = invoice.date_invoice and invoice.date_invoice.strftime(
                "%Y%m%d")
            new_individual_internal_ref = ''
            if invoice.partner_id and invoice.partner_id.individual_internal_ref and '-' in invoice.partner_id.individual_internal_ref:
                new_individual_internal_ref = invoice.partner_id.individual_internal_ref.replace('-', '')
            paylod = """H|%s|%s|%s|%s|
S|%s|%s|%s|%s|%s|
M|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|
P|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n""" % (
                # Header (Start of Message) Record – Type ‘H’
                invoice.id or '', 120, 'TOMS2', '',
                # Service Provider Record – Type ‘S’
                current_date_time, practice_number or '', practice_name or '', '',
                self.env.user.company_id.vat or '',
                # Member Record – Type ‘M’
                invoice.partner_id.id_number or '', invoice.partner_id.title.shortcut or '',
                invoice.partner_id.initials or 'N',
                invoice.partner_id.surname or '',
                invoice.partner_id.name or '', invoice.partner_id.medical_aid_no or '', 'N',
                new_individual_internal_ref,
                invoice.partner_id.street or '', invoice.partner_id.street2 or '', invoice.partner_id.city or '',
                invoice.partner_id.zip or '',
                invoice.partner_id.mobile or '', invoice.partner_id.option_id.name or '', '',
                invoice.partner_id.medical_aid_id.name or '', invoice.partner_id.medical_aid_id.ref or '', '03',
                'network',
                invoice.partner_id.medical_aid_id.destination_code or '',
                # Patient Record – Type ‘P’
                invoice.patient_id.dependent_code or '', invoice.patient_id.surname or '',
                invoice.patient_id.initials or '',
                invoice.patient_id.name or '', birthday or '',
                invoice.patient_id.gender and invoice.patient_id.gender.upper() or '', '',
                invoice.patient_id.id_number or '', recall_exam_date or '', '', '', '', '', '', '', '', '',
                '', '01', '', '', invoice.id or '',
            )
            count = 1
            # wdb.set_trace()
            for line in invoice.invoice_line_ids:
                if not line.product_id.default_code:
                    raise MissingError("Tariff Code/Ref is missing")
                # T
                paylod += """T|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n""" % (
                    # Treatment Record – Type ‘T’
                    count, invoice_date, invoice_date, '', invoice.id or '',
                    line.id, '02',
                    int(line.quantity * 100 or 0), '06', line.product_id.default_code or '', '05', '',
                    '', '10',
                    line.product_id.name or '',
                    '',
                    '', '', '',
                    '', '', '', '', '', '', '11')
                # OP records
                if line.final_rx_id:
                    rx_data = line.final_rx_id

                    # Left side values
                    op_count = 1
                    L_v12_val = ''
                    L_v13_val = ''
                    if rx_data.od_prism:
                        L_v12_val = int(str(rx_data.od_prism)[0]) * 100
                        if len(rx_data.od_prism) > 1:
                            L_v13_val = rx_data.od_prism[1:]
                    # v12_val = rx_data.od_prism.isdigit()
                    paylod += """OP|{v2}|{v3}|{v4}|{v5}|{v6}|{v7}|{v8}|{v9}|{v10}|{v11}|{v12}|{v13}|{v14}|{v15}|\n""".format(
                        # OP Record – Type ‘OP’
                        v2=op_count,
                        v3=line.product_id.seller_ids and line.product_id.seller_ids[
                            0].display_name or "None Specified",
                        v4=line.product_id.name or '',
                        v5='',
                        v6='',
                        v7='L',
                        v8=int(rx_data.od_syh * 100) or '',
                        v9=int(rx_data.od_cyl * 100) or '',
                        v10=int(rx_data.od_axis * 100) or '',
                        v11=int(rx_data.od_add * 100) or '',
                        v12=L_v12_val,
                        v13=L_v13_val, v14='',
                        v15=line.product_id.name or '',
                    )

                    # Right side values
                    op_count += 1
                    R_v12_val = ''
                    R_v13_val = ''
                    if rx_data.os_prism:
                        R_v12_val = int(rx_data.os_prism[0]) * 100
                        if len(rx_data.os_prism) > 1:
                            R_v13_val = rx_data.os_prism[1:]
                    paylod += """OP|{v2}|{v3}|{v4}|{v5}|{v6}|{v7}|{v8}|{v9}|{v10}|{v11}|{v12}|{v13}|{v14}|{v15}|\n""".format(
                        # OP Record – Type ‘OP’
                        v2=op_count,
                        v3=line.product_id.seller_ids and line.product_id.seller_ids[
                            0].display_name or "None Specified",
                        v4=line.product_id.name or '',
                        v5='',
                        v6='',
                        v7='R',
                        v8=int(rx_data.os_syh * 100) or '',
                        v9=int(rx_data.os_cyl * 100) or '',
                        v10=int(rx_data.os_axis * 100) or '',
                        v11=int(rx_data.os_add * 100) or '',
                        v12=R_v12_val,
                        v13=R_v13_val, v14='',
                        v15=line.product_id.name or '',
                    )

                # DR
                paylod += """DR|%s|%s|%s|%s|%s|%s|%s|%s|\n""" % (
                    practice_number or '', practice_name or '', '01',
                    invoice.optometrist_id.op_number or '', '01', '', '', '',
                )
                d_count = 1

                for each in line.icd_codes_ids:
                    paylod += """D|%s|%s|%s|%s|%s|\n""" % (  # D
                        '01', '01', each.code, '', '01' if d_count == 1 else '02',)
                    d_count += 1
                paylod += """Z|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\n""" % (
                    # Treatment Financial Record – Type ‘Z’
                    int(line.price_total * 100),
                    int(line.price_total * 100), '', '', '', '', '', '', '',
                    int(line.price_total * 100), '', '', '', '', '',
                    int(line.price_total * 100), '',
                )
                count += 1
            paylod += """F|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|
E|%s|%s|%s|\n""" % (
                # Claim Financial Record – Type ‘F’
                int(invoice.amount_total * 100), int(invoice.amount_total * 100), int(invoice.amount_total * 100),
                '', '', '', '',
                invoice.id or '',
                '', int(invoice.amount_total * 100), '',
                # Footer (End of Message) Record – Type ‘E’
                invoice.id or '', '1', int(invoice.amount_total * 100),
            )
            invoice.write({'comment':paylod.strip()})
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
                             <txType>303</txType>
                             <mode>%s</mode>
                             <txVersion>%s</txVersion>
                             <userRef>%s</userRef>
                             <payload>%s</payload>
                          </v2:submitOperation>
                       </soapenv:Body>
                    </soapenv:Envelope>
                    """ % (
                username, password, package, invoice.partner_id.plan_option_id.destination_code, mode,
                txversion,
                invoice.id, paylod)
            headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
            response = requests.post(url, headers=headers, data=xml1.encode('utf-8'))
            response_string = ET.fromstring(response.content)
            data_dict = {}
            responsepayload = False
            for node in response_string.iter():
                if node.tag == 'swref':
                    data_dict.update({'switch_reference': node.text})
                    invoice.user_ref = node.text
                elif node.tag == 'responsePayload':
                    data_dict.update({'response_payload': node.text})
                    responsepayload = node.text
                elif node.tag == 'message':
                    raise Warning(_(node.text))
                else:
                    data_dict.update({str(node.tag): node.text})
            data_dict.update(
                {'invoice_id': self.id, 'destination_code': invoice.partner_id.plan_option_id.destination_code or '',
                 'user_reference': invoice.id or '', 'generated_payload': paylod,
                 'response_payload_date': datetime.now()})
            claim_reversal_id = self.env['mediswitch.submit.claim'].create(data_dict)
            if responsepayload:
                order_lines = []
                rejection_count = ''
                lines = responsepayload.split("\n")
                strings = ("Invalid Missing", "Invalid")
                if any(s in lines[0] for s in strings):
                    raise Warning(_(lines[0]))
                if lines and lines[0] and lines[0].startswith('H'):
                    flag = 1
                    message = ''
                    for line in lines:
                        split_line = line.split("|")
                        if line.startswith('S'):
                            if int(line.split("|")[5]) > 0:
                                flag = 1
                        if line.startswith('R') and flag == 1:
                            rejection_count += '\n' + split_line[2] + ' - ' + split_line[1]
                        if line.startswith('FR') and flag == 1:
                            rejection_count ='\n' +  split_line[1]

                        if line.startswith('P') and flag == 1:
                            message11, message2, message3 = self.claim_messages(split_line[13], split_line[14],
                                                                                split_line[15])
                            reversal_accepted = message11
                            invoice.claim_level_mediswitch_status = split_line[13]
                            if split_line[13] == '07':
                                message11 = 'Claim Reversal Rejected'
                            message = message3 + ' - ' + message11 + ', from ' + message2 + '\n'
                    claim_reversal_id.response_error = rejection_count
                    for each in invoice.invoice_line_ids:
                        each.approved_amount = 0
                        each.balance_amount = 0
                        each.claim_status = message11
                        line = [0, 0, {'product_id': each.product_id.id,
                                       'quantity': each.quantity,
                                       'price_unit': each.price_unit,
                                       'approved_amount': 0,
                                       'balance_amount': 0,
                                       'tax_ids': [[4, id.id] for id in
                                                   each.invoice_line_tax_ids] if each.invoice_line_tax_ids else False,
                                       'price_subtotal': each.price_subtotal}]
                        order_lines.append(line)

                    view_id = self.env['response.reversal.wizard'].sudo().create(
                        {'name': message, 'response_error': rejection_count, 'practise_name': practice_name,
                         'practise_number': practice_number, 'Medical_aid': invoice.partner_id.medical_aid_id.name,
                         'patient_name': invoice.patient_id.id, 'patient_dob': invoice.patient_id.birth_date,
                         'invoice_id': invoice.id or '', 'member_no': invoice.partner_id.medical_aid_no,
                         'claim_status_reversal_lines_ids': order_lines
                         })
                    if reversal_accepted:
                        if reversal_accepted == 'Claim Reversal Accepted':
                            move_id = self.env['account.move.line'].search([('invoice_id', '=', invoice.id)], limit=1)
                            move_id.remove_move_reconcile()
                            payment_id = self.env['account.payment'].search([('communication', '=', invoice.number)],
                                                                            limit=1)
                            payment_id.cancel()
                            payment_id.payment_transaction_id.write({'state':'cancel'})
                            credit_note_id = self.env['account.invoice.refund'].create(
                                {'filter_refund': 'cancel', 'description': 'Claim Reversal', 'date': date.today()})
                            credit_note_id.with_context({'active_ids': invoice.id}).invoice_refund()

                    return {
                        'name': 'Response Reversal Wizard',
                        'type': 'ir.actions.act_window',
                        'res_model': 'response.reversal.wizard',
                        'res_id': view_id.id,
                        'view_id': self.env.ref('mediswitch_integration.response_reversal_wizard').id,
                        'view_mode': 'form',
                        'target': 'new',
                    }

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def id_msv(self):
        current_date_time = datetime.now().strftime("%Y%m%d%H%M")
        ir_config_obj = self.env['ir.config_parameter']
        practice_number = ir_config_obj.sudo().get_param('mediswitch_integration.practice_number')
        practice_name = ir_config_obj.sudo().get_param('mediswitch_integration.practice_name')
        for partner in self:
            if not partner.id_number:
                raise Warning(_('Please enter the ID Number of the patient before you can perform the ID MSV'))
            if not partner.medical_aid_id.msv_allowed:
                raise Warning(_('Sorry, MSV is not enabled for the patients Medical Aid.'))
            if not partner.surname:
                raise MissingError("Member Surname is missing")
            if not partner.name:
                raise MissingError("Member Name is missing")
            if not partner.individual_internal_ref:
                raise MissingError("Member Internal Ref is missing")
            paylod = """H|%s|%s|%s|
S|%s|%s|%s|%s|
M|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|
E|%s|%s|\n""" % (
                # P|%s|%s|%s|%s|%s|%s|%s|%s|
                # Header (Start of Message) Record – Type ‘H’
                partner.id or '', 121, 'TOMS:2',
                # Service Provider Record – Type ‘S’
                current_date_time, practice_number or '', practice_name or '', '',
                # Member Record – Type ‘M’
                '1', partner.id_number or '',
                partner.title.name or 'N',
                partner.initials or 'N',
                partner.surname or '',
                partner.name or '', '', 'N', '',
                '',
                # Footer Record – Type ‘E’
                partner.id or '', '1',
            )
            partner.write({'payload_description': paylod})
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
                username, password, package, partner.plan_option_id.destination_code, mode,
                txversion,
                partner.id, paylod)
            try:
                headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
                response = requests.post(url, headers=headers, data=xml1.encode('utf-8'))
                response_string = ET.fromstring(response.content)
            except Exception as e:
                raise Warning(_('502 Bad Gateway'))
            responsepayload = False
            wizard_data = {'partner_id': partner.id,'msv_type':'id_msv','request_payload':paylod}
            for node in response_string.iter():
                if node.tag == 'responsePayload':
                    responsepayload = node.text
            if responsepayload:
                wizard_data.update({"response_payload":responsepayload})
                lines = responsepayload.split("\n")
                list1 = []
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
                                dob = date(year=int(split_line[5][0:4]), month=int(split_line[5][4:6]),
                                           day=int(split_line[5][6:9]))
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
                                'membership_number': split_line[4],
                                'medical_scheme_name': split_line[12],
                                'plan_name': split_line[15],
                                'option_name': split_line[15]
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
                                'validation_code': validation_code or False,
                                'disclaimer': split_line[3] or False,
                                'status_code_description': split_line[5] or False,
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
    def surname_dob_msv(self):
        current_date_time = datetime.now().strftime("%Y%m%d%H%M")
        ir_config_obj = self.env['ir.config_parameter']
        practice_number = ir_config_obj.sudo().get_param('mediswitch_integration.practice_number')
        practice_name = ir_config_obj.sudo().get_param('mediswitch_integration.practice_name')
        for partner in self:
            if not partner.surname and not partner.birth_date:
                raise Warning(_('Please enter the Surname and DOB of the patient before you can perform the Surname DOB MSV'))
            if not partner.medical_aid_id.msv_allowed:
                raise Warning(_('Sorry, MSV is not enabled for the patients Medical Aid.'))
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
P|%s|%s|%s|%s|%s|%s|%s|%s|
E|%s|%s|\n""" % (
                # P|%s|%s|%s|%s|%s|%s|%s|%s|
                # Header (Start of Message) Record – Type ‘H’
                partner.id or '', 121, 'TOMS:2',
                # Service Provider Record – Type ‘S’
                current_date_time, practice_number or '', practice_name or '', '',
                # Member Record – Type ‘M’
                '1', '',
                partner.title.name or 'N',
                partner.initials or 'N',
                partner.surname or '',
                partner.name or '', '', 'N', partner.medical_aid_id.destination_code or '','',
                # # Patient Record – Type ‘P’
                partner.dependent_code or '', partner.surname or '',
                partner.initials or '',
                partner.name or '', birthday or '',
                gender or '', '',
                partner.id_number or '',
                # Footer Record – Type ‘E’
                partner.id or '', '1',
            )
            partner.write({'payload_description': paylod})
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
                username, password, package, partner.plan_option_id.destination_code, mode,
                txversion,
                partner.id, paylod)
            try:
                headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
                response = requests.post(url, headers=headers, data=xml1.encode('utf-8'))
                response_string = ET.fromstring(response.content)
            except Exception as e:
                raise Warning(_('502 Bad Gateway'))
            responsepayload = False
            wizard_data = {'partner_id': partner.id, 'msv_type': 'sur_dob_msv', 'request_payload': paylod}
            for node in response_string.iter():
                if node.tag == 'responsePayload':
                    responsepayload = node.text
            if responsepayload:
                wizard_data.update({"response_payload": responsepayload})
                lines = responsepayload.split("\n")
                list1 = []
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
                                dob = date(year=int(split_line[5][0:4]), month=int(split_line[5][4:6]),
                                           day=int(split_line[5][6:9]))
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
                                'membership_number': split_line[4],
                                'medical_scheme_name': split_line[12],
                                'plan_name': split_line[15],
                                'option_name': split_line[15]
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
                                'validation_code': validation_code or False,
                                'disclaimer': split_line[3] or False,
                                'status_code_description': split_line[5] or False,
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

class IdMsv(models.Model):
    _name = "id.msv"
    _description = "MSV to mediswitch by ID"

    name = fields.Char(readonly=1)

    @api.multi
    def id_msv(self):
        current_date_time = datetime.now().strftime("%Y%m%d%H%M")
        ir_config_obj = self.env['ir.config_parameter']
        practice_number = ir_config_obj.sudo().get_param('mediswitch_integration.practice_number')
        practice_name = ir_config_obj.sudo().get_param('mediswitch_integration.practice_name')
        for partner in self.env.context.get('active_ids'):
            partner = self.env['res.partner'].browse(partner)
            if not partner.id_number:
                raise Warning(_('Please enter the ID Number of the patient before you can perform the ID MSV'))
            if not partner.medical_aid_id.msv_allowed:
                raise Warning(_('Sorry, MSV is not enabled for the patients Medical Aid.'))
            if not partner.surname:
                raise MissingError("Member Surname is missing")
            if not partner.name:
                raise MissingError("Member Name is missing")
            if not partner.individual_internal_ref:
                raise MissingError("Member Internal Ref is missing")
            paylod = """H|%s|%s|%s|
S|%s|%s|%s|%s|
M|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|
E|%s|%s|\n""" % (
                # P|%s|%s|%s|%s|%s|%s|%s|%s|
                # Header (Start of Message) Record – Type ‘H’
                partner.id or '', 121, 'TOMS:2',
                # Service Provider Record – Type ‘S’
                current_date_time, practice_number or '', practice_name or '', '',
                # Member Record – Type ‘M’
                '1', partner.id_number or '',
                partner.title.name or 'N',
                partner.initials or 'N',
                partner.surname or '',
                partner.name or '', '', 'N', '',
                '',
                # Footer Record – Type ‘E’
                partner.id or '', '1',
            )
            partner.write({'payload_description': paylod})
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
                username, password, package, partner.plan_option_id.destination_code, mode,
                txversion,
                partner.id, paylod)
            try:
                headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
                response = requests.post(url, headers=headers, data=xml1.encode('utf-8'))
                response_string = ET.fromstring(response.content)
            except Exception as e:
                raise Warning(_('502 Bad Gateway'))
            responsepayload = False
            wizard_data = {'partner_id': partner.id, 'msv_type': 'id_msv', 'request_payload': paylod}
            for node in response_string.iter():
                if node.tag == 'responsePayload':
                    responsepayload = node.text
            if responsepayload:
                wizard_data.update({"response_payload": responsepayload})
                lines = responsepayload.split("\n")
                list1 = []
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
                                dob = date(year=int(split_line[5][0:4]), month=int(split_line[5][4:6]),
                                           day=int(split_line[5][6:9]))
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
                                'membership_number': split_line[4],
                                'medical_scheme_name': split_line[12],
                                'plan_name': split_line[15],
                                'option_name': split_line[15]
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
                                'validation_code': validation_code or False,
                                'disclaimer': split_line[3] or False,
                                'status_code_description': split_line[5] or False,
                            })
            partner.msv_later_button = False
            wizard_id = self.env['msv.response'].create(wizard_data)
            if list1:
                for data in list1:
                    data.update({'msv_response_id': wizard_id.id})
                    self.env['msv.members'].create(data)
            partner.msv_latest_date = wizard_id.create_date


class SurnameDobMsv(models.Model):
    _name = "surname.dob.msv"
    _description = "Submit MSV by Date of Birth and Surname"

    name = fields.Char(readonly=1)

    @api.multi
    def surname_dob_msv(self):
        current_date_time = datetime.now().strftime("%Y%m%d%H%M")
        ir_config_obj = self.env['ir.config_parameter']
        practice_number = ir_config_obj.sudo().get_param('mediswitch_integration.practice_number')
        practice_name = ir_config_obj.sudo().get_param('mediswitch_integration.practice_name')
        for partner in self.env.context.get("active_ids"):
            partner = self.env['res.partner'].browse(partner)
            if not partner.surname and not partner.birth_date:
                raise Warning(
                    _('Please enter the Surname and DOB of the patient before you can perform the Surname DOB MSV'))
            if not partner.medical_aid_id.msv_allowed:
                raise Warning(_('Sorry, MSV is not enabled for the patients Medical Aid.'))
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
P|%s|%s|%s|%s|%s|%s|%s|%s|
E|%s|%s|\n""" % (
                # P|%s|%s|%s|%s|%s|%s|%s|%s|
                # Header (Start of Message) Record – Type ‘H’
                partner.id or '', 121, 'TOMS:2',
                # Service Provider Record – Type ‘S’
                current_date_time, practice_number or '', practice_name or '', '',
                # Member Record – Type ‘M’
                '1', '',
                partner.title.name or 'N',
                partner.initials or 'N',
                partner.surname or '',
                partner.name or '', '', 'N', partner.medical_aid_id.destination_code or '', '',
                # Patient Record – Type ‘P’
                partner.dependent_code or '', partner.surname or '',
                partner.initials or '',
                partner.name or '', birthday or '',
                gender or '', '',
                partner.id_number or '',
                # Footer Record – Type ‘E’
                partner.id or '', '1',
            )
            partner.write({'payload_description': paylod})
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
                username, password, package, partner.plan_option_id.destination_code, mode,
                txversion,
                partner.id, paylod)
            try:
                headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
                response = requests.post(url, headers=headers, data=xml1.encode('utf-8'))
                response_string = ET.fromstring(response.content)
            except Exception as e:
                raise Warning(_('502 Bad Gateway'))
            responsepayload = False
            wizard_data = {'partner_id': partner.id, 'msv_type': 'sur_dob_msv', 'request_payload': paylod}
            for node in response_string.iter():
                if node.tag == 'responsePayload':
                    responsepayload = node.text
            if responsepayload:
                wizard_data.update({"response_payload": responsepayload})
                lines = responsepayload.split("\n")
                list1 = []
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
                                dob = date(year=int(split_line[5][0:4]), month=int(split_line[5][4:6]),
                                           day=int(split_line[5][6:9]))
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
                                'membership_number': split_line[4],
                                'medical_scheme_name': split_line[12],
                                'plan_name': split_line[15],
                                'option_name': split_line[15]
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
                                'validation_code': validation_code or False,
                                'disclaimer': split_line[3] or False,
                                'status_code_description': split_line[5] or False,
                            })
            partner.msv_later_button = False
            wizard_id = self.env['msv.response'].create(wizard_data)
            if list1:
                for data in list1:
                    data.update({'msv_response_id': wizard_id.id})
                    self.env['msv.members'].create(data)
            partner.msv_latest_date = wizard_id.create_date
