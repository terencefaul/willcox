
from odoo import fields, models, api , _
from suds.wsse import Security, UsernameToken
from suds.client import Client
from datetime import datetime,date
from odoo.http import request
from odoo.exceptions import MissingError , Warning
import xml.etree.ElementTree as ET
import time
import json
import requests

class MediswitchSubmitClaim(models.Model):
    _name = "mediswitch.submit.claim"
    _description='Submit the claim to the mediswitch'
    _rec_name = 'name'

    name = fields.Char(string="Name")
    response_payload_date = fields.Datetime(string="Date")
    destination_code = fields.Char(string="Destination Code")
    user_reference = fields.Integer(string="User Reference")
    generated_payload = fields.Text(string="Payload")
    status = fields.Char(string="Status")
    switch_reference = fields.Char(string="Switch Reference")
    retry = fields.Integer(string="Retry")
    response_payload = fields.Text(string="Response Payload")
    force=fields.Integer(string="Force")
    invoice_id = fields.Many2one("account.invoice",string="Invoice Ref",readonly="1")
    fetch_claim_id=fields.One2many("mediswitch.fetch.claim",'claim_ref_id')
    status_morefiles = fields.Char(string="Status Of MoreFiles",invisible="1")
    response_error = fields.Text(string="Response Error")

    @api.multi
    def fetch_operations(self):
        if self.env.context.get('fetch_response'):
            invoice_ids = self.invoice_id
        else:
            invoice_ids = self.env['account.invoice'].search([('claim_level_mediswitch_status', 'in', ['01', '02'])])
        if self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.for_what') == 'test':
            username = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.user_name_test')
            password = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.password_test')
            package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_test')
            url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.test_url')
        else:
            username = self.env['ir.config_parameter'].sudo().get_param(
                'mediswitch_integration.user_name_production')
            password = self.env['ir.config_parameter'].sudo().get_param(
                'mediswitch_integration.password_production')
            package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_production')
            url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.production_url')
        for invoice in invoice_ids:
            xml = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v2="http://gateway.switchonline.co.za/MediswitchGateway/v2">
                           <soapenv:Header/>
                           <soapenv:Body>
                              <v2:fetchOperation>
                                 <user>%s</user>
                                 <passwd>%s</passwd>
                                 <package>%s</package>
                                 <txType>302</txType>
                                 <swref>%s</swref>
                                 <force>%s</force>
                              </v2:fetchOperation>
                           </soapenv:Body>
                        </soapenv:Envelope>""" % (
                username, password, package, invoice.user_ref, 0)
            headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
            response = requests.post(url, headers=headers, data=xml.encode('utf-8'))
            response_string = ET.fromstring(response.content)
            data_dict = {}
            responsepayload = False

            for node in response_string.iter():
                if node.tag == 'originalSwref':
                    data_dict.update({'origial_swref': node.text})
                elif node.tag == 'responsePayload':
                    data_dict.update({'response_payload': node.text})
                elif node.tag == 'feedbackType':
                    data_dict.update({'feedback_type': node.text})
                elif node.tag == 'feedbackVersion':
                    data_dict.update({'feedback_version': node.text})
                elif node.tag == 'moreFiles':
                    data_dict.update({'morefiles': int(node.text)})
                elif node.tag == 'originalUserRef':
                    data_dict.update({'original_userref': node.text})
                elif node.tag == 'originalDataSetId':
                    if node.text:
                        data_dict.update({'original_dataset_id': int(node.text)})
                elif node.tag == 'fileName':
                    data_dict.update({'filename': node.text})
                elif node.tag == 'fileDate':
                    data_dict.update({'filedate': node.text or date.today()})
                elif node.tag == 'message':
                    raise Warning(_(node.text))
                else:
                    data_dict.update({str(node.tag): node.text})
            claim_id = self.env['mediswitch.submit.claim'].search([('switch_reference', '=', invoice.user_ref)],
                                                                  limit=1)
            data_dict.update(
                {'claim_ref_id': claim_id.id})
            fetch_id = self.env['mediswitch.fetch.claim'].create(data_dict)
            if responsepayload:
                claim_status_lines = []
                lines = responsepayload.split("\n")
                strings = ("Invalid Missing", "Invalid")
                if any(s in lines[0] for s in strings):
                    raise Warning(_(lines[0]))
                if lines and lines[0] and lines[0].startswith('H'):
                    flag = 1
                    treatment_line = 0
                    balance_price = 0
                    approved_price = 0
                    total_approved_price = 0
                    list1 = []
                    number = 0
                    message = ''
                    for line in lines:
                        split_line = line.split("|")
                        if line.startswith('S'):
                            if int(line.split("|")[5]) >= 0:
                                flag = 1
                        if line.startswith('G'):
                            rejection_count += "\n" + split_line[1]
                        if line.startswith('R') and flag == 1:
                            rejection_count = split_line[2] + ' - ' + split_line[1]
                            fetch_id.response_error = rejection_count
                        if line.startswith('FR') and flag == 1:
                            rejection_count = split_line[1]
                            fetch_id.response_error = rejection_count
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
                    if total_approved_price:
                        invoice.action_invoice_open()
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
                        number += 1

    @api.model
    def create(self, vals):
        res = super(MediswitchSubmitClaim, self).create(vals)
        name = self.env['ir.sequence'].next_by_code('claim_sequence')
        if res.invoice_id and res.invoice_id.sequence_number_next and res.invoice_id.sequence_number_next_prefix:
            res.name = name + '-' + res.invoice_id.sequence_number_next_prefix + res.invoice_id.sequence_number_next
        else:
            res.name = name
        return res

class MediswitchFetchClaim(models.Model):
    _name="mediswitch.fetch.claim"
    _description="fetch the response of the mediswitch"
    _rec_name="origial_swref"

    claim_ref_id=fields.Many2one("mediswitch.submit.claim",string="Claim Ref",readonly="1")
    status=fields.Char(string="Fetch Status")
    feedback_type=fields.Char(string="Feedback Type")
    feedback_version=fields.Char(string="FeedBack Version")
    morefiles=fields.Integer(string="More Files")
    origial_swref=fields.Char(string="Switch Reference")
    original_userref=fields.Char(string="User Reference")
    original_dataset_id=fields.Integer(string="DataSet Id")
    filename=fields.Char(string="File Name")
    filedate=fields.Date(string="File Date")
    response_payload=fields.Text(string="Response Payload")
    response_error = fields.Text(string="Response Error")


class Globalfetch(models.Model):
    _name = "global.fetch.claim"
    _description = "To fetch claim from mediswitch"

    name = fields.Char(string="Status")
    f_type = fields.Char(string="feedbackType")
    f_version = fields.Char(string="feedbackVersion")
    morefiles= fields.Char(string="moreFiles")
    originalswref= fields.Char(string="originalSwref")
    originaluserref= fields.Char(string="originalUserRef")
    originaldatasetid= fields.Char(string="originalDataSetId")
    filename= fields.Char(string="fileName")
    filedate= fields.Char(string="fileDate")
    responsepayload= fields.Char(string="responsePayload")
    txtype= fields.Char(string="txType")
    swref= fields.Char(string="swRef")
    force= fields.Integer(string="force", default=0)
    invoice_id = fields.Many2one("account.invoice", string="Invoice Ref")

    @api.model
    def create_global_fetch_record(self):
        view_id = self.env.ref('mediswitch_integration.global_fetch_claims_form_view_1').id
        return view_id

    def fetch_response(self):
        for partner in self:
            if self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.for_what') == 'test':
                username = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.user_name_test')
                password = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.password_test')
                package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_test')
                url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.test_url')
            else:
                username = self.env['ir.config_parameter'].sudo().get_param(
                    'mediswitch_integration.user_name_production')
                password = self.env['ir.config_parameter'].sudo().get_param(
                    'mediswitch_integration.password_production')
                package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_production')
                url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.production_url')
            xml1 = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v2="http://gateway.switchonline.co.za/MediswitchGateway/v2">
                                           <soapenv:Header/>
                                           <soapenv:Body>
                                              <v2:fetchOperation>
                                                 <user>%s</user>
                                                 <passwd>%s</passwd>
                                                 <package>%s</package>
                                                 <txType>%s</txType>
                                                 <swref>%s</swref>
                                                 <force>%s</force>
                                              </v2:fetchOperation>
                                           </soapenv:Body>
                                        </soapenv:Envelope>
                                        """ % (
                username, password, package, partner.txtype or '',partner.swref or '',partner.force or '0')
            response1 = False
            try:
                headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
                response = requests.post(url, headers=headers, data=xml1.encode('utf-8'))
                response1 = """<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
                                   <env:Header/>
                                   <env:Body>
                                      <v2:fetchOperationResponse xmlns:v2="http://gateway.switchonline.co.za/MediswitchGateway/v2">
                                         <response xmlns:ns2="http://gateway.switchonline.co.za/MediswitchGateway/v1">
                                            <status>OK</status>
                                            <feedbackType>303</feedbackType>
                                            <feedbackVersion>121</feedbackVersion>
                                            <moreFiles>1</moreFiles>
                                            <originalSwref>0-c-e61da52000</originalSwref>
                                            <originalUserRef>120</originalUserRef>
                                            <originalDataSetId/>
                                            <fileName>0-c-e61da71000.processed</fileName>
                                            <fileDate/>
                                            <responsePayload>H|120|
                                S|202004171211|7025807|Spectacle Warehouse Atterbury||001|
                                M|SAVVA|HELEN SAVVA|102600810|SWHFO000077|DISCOVERY HEALTH|S0680|DHEA0000||
                                P|00|SAVVA|H|HELEN SAVVA|19611116|6111160194089||||01|120|01|07|01|01|
                                T|202002110000|202002110000||120|625||02|100|11001||Optometric Examination|||07|01|01|
                                Z|0|0||||||||45610||||||||||
                                T|202002110000|202002110000||120|626||02|100|93950||Comprehensive AEI Screening and Report- Fundus Photo Only|||07|01|01|
                                Z|0|0||||||||3500||||||||||
                                T|202002110000|202002110000||120|627||02|100|86LT112||Rodenstock Progressiv Pure Life Free? 1.60 Uncoate|||07|01|01|
                                Z|0|0||||||||185200||||||||||
                                T|202002110000|202002110000||120|628||02|100|86BS001||Varifocal Distance to Near|||07|01|01|
                                Z|0|0||||||||151500||||||||||
                                T|202002110000|202002110000||120|629||02|100|86LT112||Rodenstock Progressiv Pure Life Free? 1.60 Uncoate|||07|01|01|
                                Z|0|0||||||||185200||||||||||
                                T|202002110000|202002110000||120|630||02|100|86BS001||Varifocal Distance to Near|||07|01|01|
                                Z|0|0||||||||151500||||||||||
                                T|202002110000|202002110000||120|631||02|100|87EL08D||Rodenstock Solitaire Balance 2|||07|01|01|
                                Z|0|0||||||||142000||||||||||
                                T|202002110000|202002110000||120|632||02|100|87EL08D||Rodenstock Solitaire Balance 2|||07|01|01|
                                Z|0|0||||||||142000||||||||||
                                T|202002110000|202002110000||120|633||02|100|40501||Spectacle Frame|||07|01|01|
                                Z|0|0||||||||410000||||||||||
                                R|SW999|Unable to reverse claim with Scheme|
                                F|0|0|0||||||||||
                                E|120|1|0|</responsePayload>
                                         </response>
                                      </v2:fetchOperationResponse>
                                   </env:Body>
                                </env:Envelope>
                """
                response_string = ET.fromstring(response1 if response1 else response.content)
                print("\n\n\n\ response string>>>--",response_string)
            except Exception as e:
                raise Warning(_('502 Bad Gateway'))
            responsepayload = False
            data = {}
            for node in response_string.iter():
                if node.tag == 'status':
                    data.update({'status':node.text})
                    partner.name = node.text
                if node.tag == 'feedbackType':
                    data.update({'feedback_type': node.text})
                    partner.f_type = node.text
                if node.tag == 'feedbackVersion':
                    data.update({'feedback_version': node.text})
                    partner.f_version = node.text
                if node.tag == 'moreFiles':
                    data.update({'morefiles': int(node.text)})
                    partner.morefiles = node.text
                if node.tag == 'originalSwref':
                    if node.text:
                        id = self.env['mediswitch.submit.claim'].search([('switch_reference','=',node.text)], limit=1)
                        if id:
                            partner.invoice_id = id.invoice_id.id
                            id.invoice_id.user_ref = id.switch_reference
                    data.update({'origial_swref': node.text,'claim_ref_id':id.id})
                    partner.originalswref = node.text
                if node.tag == 'originalUserRef':
                    data.update({'original_userref': node.text})
                    partner.originaluserref = node.text
                if node.tag == 'originalDataSetId':
                    data.update({'original_dataset_id': node.text})
                    partner.originaldatasetid = node.text
                if node.tag == 'fileName':
                    data.update({'filename': node.text})
                    partner.filename = node.text
                if node.tag == 'fileDate':
                    # data.update({'filedate': node.tag})
                    partner.filedate = node.text
                if node.tag == 'responsePayload':
                    data.update({'response_payload': node.text})
                    partner.responsepayload = node.text
            self.env['mediswitch.fetch.claim'].create(data)
            if responsepayload and id:
                claim_status_lines = []
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
                        if line.startswith('S') and split_line[0] == 'S':
                            if int(line.split("|")[5]) >= 0:
                                flag = 1
                        if line.startswith('R') and split_line[0] == 'R' and flag == 1:
                            rejection_count += "\n" + split_line[2] + ' - ' + split_line[1]
                        if line.startswith('FR') and split_line[0] == 'FR' and flag == 1:
                            rejection_count += "\n" + split_line[1]
                        if line.startswith('G') and split_line[0] == 'G':
                            rejection_count += "\n" + split_line[1]
                        if line.startswith('P') and split_line[0] == 'P' and flag == 1:
                            message11, message2, message3 = self.claim_messages(split_line[13], split_line[14],
                                                                                split_line[15])
                            message = message3 + ' - ' + message11 + ', from ' + message2 + '\n'
                            invoice.claim_level_mediswitch_status = split_line[13]
                        if line.startswith('T') and split_line[0] == 'T' and flag == 1:
                            treatment_line += 1
                            message1, message2, message3 = self.claim_messages(split_line[14], split_line[15],
                                                                               split_line[16])
                            claim_status_lines.append(message1)
                        if line.startswith('Z') and split_line[0] == 'Z':
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
                    for each in id.invoice_id.invoice_line_ids:
                        if len(claim_status_lines) > 0 and claim_status_lines[number]:
                            status = claim_status_lines[number]
                        else:
                            status = ""
                        each.approved_amount = list1[number].get('approve')
                        each.balance_amount = list1[number].get('balance')
                        each.claim_status = status
                        number += 1
            return {
                'name': 'Global Fetch Response Wizard',
                'type': 'ir.actions.act_window',
                'res_model': 'global.fetch.claim',
                'res_id': partner.id,
                'view_id': self.env.ref('mediswitch_integration.global_fetch_claims_form_view_1').id,
                'view_mode': 'form',
                'target': 'new',
            }
        
    @api.model
    def fetch_response_cron(self):
        if self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.for_what') == 'test':
            username = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.user_name_test')
            password = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.password_test')
            package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_test')
            url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.test_url')
        else:
            username = self.env['ir.config_parameter'].sudo().get_param(
                'mediswitch_integration.user_name_production')
            password = self.env['ir.config_parameter'].sudo().get_param(
                'mediswitch_integration.password_production')
            package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_production')
            url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.production_url')
        xml1 = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v2="http://gateway.switchonline.co.za/MediswitchGateway/v2">
                                       <soapenv:Header/>
                                       <soapenv:Body>
                                          <v2:fetchOperation>
                                             <user>%s</user>
                                             <passwd>%s</passwd>
                                             <package>%s</package>
                                             <txType>%s</txType>
                                             <swref>%s</swref>
                                             <force>%s</force>
                                          </v2:fetchOperation>
                                       </soapenv:Body>
                                    </soapenv:Envelope>
                                    """ % (
            username, password, package, '', '', '0')
        response1 = False
        try:
            headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
            response = requests.post(url, headers=headers, data=xml1.encode('utf-8'))
            response1 = """<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
                               <env:Header/>
                               <env:Body>
                                  <v2:fetchOperationResponse xmlns:v2="http://gateway.switchonline.co.za/MediswitchGateway/v2">
                                     <response xmlns:ns2="http://gateway.switchonline.co.za/MediswitchGateway/v1">
                                        <status>OK</status>
                                        <feedbackType>303</feedbackType>
                                        <feedbackVersion>121</feedbackVersion>
                                        <moreFiles>1</moreFiles>
                                        <originalSwref>0-c-e61da52000</originalSwref>
                                        <originalUserRef>120</originalUserRef>
                                        <originalDataSetId/>
                                        <fileName>0-c-e61da71000.processed</fileName>
                                        <fileDate/>
                                        <responsePayload>H|120|
                            S|202004171211|7025807|Spectacle Warehouse Atterbury||001|
                            M|SAVVA|HELEN SAVVA|102600810|SWHFO000077|DISCOVERY HEALTH|S0680|DHEA0000||
                            P|00|SAVVA|H|HELEN SAVVA|19611116|6111160194089||||01|120|01|07|01|01|
                            T|202002110000|202002110000||120|625||02|100|11001||Optometric Examination|||07|01|01|
                            Z|0|0||||||||45610||||||||||
                            T|202002110000|202002110000||120|626||02|100|93950||Comprehensive AEI Screening and Report- Fundus Photo Only|||07|01|01|
                            Z|0|0||||||||3500||||||||||
                            T|202002110000|202002110000||120|627||02|100|86LT112||Rodenstock Progressiv Pure Life Free? 1.60 Uncoate|||07|01|01|
                            Z|0|0||||||||185200||||||||||
                            T|202002110000|202002110000||120|628||02|100|86BS001||Varifocal Distance to Near|||07|01|01|
                            Z|0|0||||||||151500||||||||||
                            T|202002110000|202002110000||120|629||02|100|86LT112||Rodenstock Progressiv Pure Life Free? 1.60 Uncoate|||07|01|01|
                            Z|0|0||||||||185200||||||||||
                            T|202002110000|202002110000||120|630||02|100|86BS001||Varifocal Distance to Near|||07|01|01|
                            Z|0|0||||||||151500||||||||||
                            T|202002110000|202002110000||120|631||02|100|87EL08D||Rodenstock Solitaire Balance 2|||07|01|01|
                            Z|0|0||||||||142000||||||||||
                            T|202002110000|202002110000||120|632||02|100|87EL08D||Rodenstock Solitaire Balance 2|||07|01|01|
                            Z|0|0||||||||142000||||||||||
                            T|202002110000|202002110000||120|633||02|100|40501||Spectacle Frame|||07|01|01|
                            Z|0|0||||||||410000||||||||||
                            R|SW999|Unable to reverse claim with Scheme|
                            F|0|0|0||||||||||
                            E|120|1|0|</responsePayload>
                                     </response>
                                  </v2:fetchOperationResponse>
                               </env:Body>
                            </env:Envelope>
            """
            response_string = ET.fromstring(response1 if response1 else response.content)
        except Exception as e:
            raise Warning(_('502 Bad Gateway'))
        responsepayload = False
        data = {}
        for node in response_string.iter():
            if node.tag == 'status':
                data.update({'status':node.text})
            if node.tag == 'feedbackType':
                data.update({'feedback_type': node.text})
            if node.tag == 'feedbackVersion':
                data.update({'feedback_version': node.text})
            if node.tag == 'moreFiles':
                data.update({'morefiles': int(node.text)})
            if node.tag == 'originalSwref':
                if node.text:
                    id = self.env['mediswitch.submit.claim'].search([('switch_reference','=',node.text)])
                    if id:
                        id.invoice_id.user_ref = id.switch_reference
                data.update({'origial_swref': node.text,'claim_ref_id':id.id if id else False})
            if node.tag == 'originalUserRef':
                data.update({'original_userref': node.text})
            if node.tag == 'originalDataSetId':
                data.update({'original_dataset_id': node.text})
            if node.tag == 'fileName':
                data.update({'filename': node.text})
            if node.tag == 'responsePayload':
                data.update({'response_payload': node.text})
        data = self.env['mediswitch.fetch.claim'].create(data)
        if responsepayload and id:
            claim_status_lines = []
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
                    if line.startswith('S') and split_line[0] == 'S':
                        if int(line.split("|")[5]) >= 0:
                            flag = 1
                    if line.startswith('R') and split_line[0] == 'R' and flag == 1:
                        rejection_count += "\n" + split_line[2] + ' - ' + split_line[1]
                    if line.startswith('FR') and split_line[0] == 'FR' and flag == 1:
                        rejection_count += "\n" + split_line[1]
                    if line.startswith('G') and split_line[0] == 'G':
                        rejection_count += "\n" + split_line[1]
                    if line.startswith('P') and split_line[0] == 'P'and flag == 1:
                        message11, message2, message3 = self.claim_messages(split_line[13], split_line[14],
                                                                            split_line[15])
                        message = message3 + ' - ' + message11 + ', from ' + message2 + '\n'
                        invoice.claim_level_mediswitch_status = split_line[13]
                    if line.startswith('T') and split_line[0] == 'T' and flag == 1:
                        treatment_line += 1
                        message1, message2, message3 = self.claim_messages(split_line[14], split_line[15],
                                                                           split_line[16])
                        claim_status_lines.append(message1)
                    if line.startswith('Z') and split_line[0] == 'Z':
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
                    number += 1



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


class MarkToMsv(models.Model):
    _name = "mark.msv"
    _description = "To mark all the customer for msv later"

    name = fields.Char(readonly=1)

    def mark_to_msv(self):
        for id in self.env.context.get('active_ids'):
            id = self.env['res.partner'].browse(id)
            if not id.msv_later_button and id.medical_aid_id.msv_allowed:
                id.msv_later_button = True

class RemoveMsv(models.Model):
    _name = "remove.mark.msv"
    _description = "To Remove all the customer from msv later"

    name = fields.Char(readonly=1)

    def remove_msv(self):
        for id in self.env.context.get('active_ids'):
            id = self.env['res.partner'].browse(id)
            if id.msv_later_button:
                id.msv_later_button = False


class BulkMsv(models.Model):
    _name = 'bulk.msv'
    _description = "To check the customer for msv in bulk"

    name = fields.Char(readonly=1)

    @api.multi
    def bulk_msv(self):
        current_date_time = datetime.now().strftime("%Y%m%d%H%M")
        ir_config_obj = self.env['ir.config_parameter']
        practice_number = ir_config_obj.sudo().get_param('mediswitch_integration.practice_number')
        practice_name = ir_config_obj.sudo().get_param('mediswitch_integration.practice_name')
        for partner in self.env['res.partner'].search([('msv_later_button','=', True),('customer','=',True)]):
            if not partner.medical_aid_id.msv_allowed:
                wizard_data.update({'name':'Sorry, MSV is not enabled for the patients Medical Aid.'})
            if not partner.surname:
                wizard_data.update({'name':"Member Surname is missing"})
            if not partner.name:
                wizard_data.update({'name':"Member Name is missing"})
            if not partner.individual_internal_ref:
                wizard_data.update({'name':"Member Internal Ref is missing"})
            paylod = """H|%s|%s|%s|
S|%s|%s|%s|%s|
M|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|
E|%s|%s|\n""" % (
                # Header (Start of Message) Record – Type ‘H’
                partner.id or '', 121, 'TOMS:2',
                # Service Provider Record – Type ‘S’
                current_date_time, practice_number or '', practice_name or '', '',
                # Member Record – Type ‘M’
                '1', '',
                partner.title.name or 'N',
                partner.initials or 'N',
                partner.surname or '',
                partner.name or '', partner.medical_aid_no or '', 'N', '',
                partner.medical_aid_id.destination_code or '',
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
            wizard_data = {'partner_id': partner.id, 'msv_type': 'msv', 'request_payload': paylod}
            for node in response_string.iter():
                if node.tag == 'responsePayload':
                    responsepayload = node.text
            list1 = []
            msv_status = ''
            if responsepayload:
                wizard_data.update({"response_payload": responsepayload})
                lines = responsepayload.split("\n")
                is_valid = False
                strings = ("Invalid Missing", "Invalid")
                if any(s in lines[0] for s in strings):
                    wizard_data.update({'name':lines[0]})
                if lines and lines[0] and lines[0].startswith('H'):
                    for line in lines:
                        if line.startswith('RV'):
                            split_line = line.split("|")
                            if split_line[1] == '01':
                                error_text = split_line[5]
                                is_valid = True
                if not is_valid:
                    if lines and lines[0] and lines[0].startswith('H'):
                        for line in lines:
                            effective_date = False
                            termination_date = False
                            if line.startswith('P'):
                                split_line = line.split("|")
                                msv_status = split_line[10] or ''
                                if split_line[5] and len(split_line[5]) == 8:

                                    dob = date(year=int(split_line[5][0:4]), month=int(split_line[5][4:6]),
                                               day=int(split_line[5][6:9]))
                                if split_line[8] and len(split_line[8]) == 8:
                                    effective_date = date(year=int(split_line[8][0:4]), month=int(split_line[8][4:6]),
                                                          day=int(split_line[8][6:9]))
                                if split_line[9] and len(split_line[9]) == 8:
                                    termination_date = date(year=int(split_line[9][0:4]), month=int(split_line[9][4:6]),
                                                            day=int(split_line[9][6:9]))
                                list1.append({
                                    'name':split_line[4] or False,
                                    'surname':split_line[2] or False,
                                    'dependent_code':split_line[1] or False,
                                    'initials':split_line[3] or False,
                                    'dob':dob or False,
                                    'id_number':split_line[6] or False,
                                    'gender':split_line[7] or False,
                                    'effective_date':effective_date,
                                    'termination_date':termination_date,
                                    'status_code_description':split_line[10] or False,
                                })
                            if line.startswith('M'):
                                split_line = line.split("|")
                                wizard_data.update({
                                    'membership_number': split_line[4] or False,
                                    'name': split_line[12] or False,
                                    'plan_name': split_line[15] or False,
                                    'option_name': split_line[15] or False
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
                else:
                    wizard_data.update({'name':error_text})
            wizard_id = self.env['msv.response'].create(wizard_data)
            if list1:
                for data in list1:
                    self.env['msv.members'].create(data.update({'msv_response_id':wizard_id.id}))
            partner.msv_latest_date = wizard_id.create_date
            partner.msv_status = msv_status or ''
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

class MsvMembers(models.Model):
    _name = "msv.members"
    _description = "To check the customer is MSV or not."

    name = fields.Char(string="Name")
    surname = fields.Char(string="Surname")
    dependent_code = fields.Char(string="Dependant Code")
    initials = fields.Char(string="Initials")
    dob = fields.Date(string="DOB")
    id_number = fields.Char(string="Id/Passport Number")
    gender = fields.Char(string="Gender")
    effective_date = fields.Date(string="Effective Date")
    termination_date = fields.Date(string="Termination Date")
    status_code_description = fields.Char(string="status Code Description")
    msv_response_id = fields.Many2one("msv.response",string="Msv response")
    operations = fields.Selection([('search', 'Search'), ('create', 'Create'), ('update', 'Update')],
                                  string="Operations", default="search")
    search_id = fields.Many2one("res.partner", string="Member")

    def search_record(self):
        if self.id_number:
            record = self.env['res.partner'].search([('id_number', '=', self.id_number)], limit=1)
            if record:
                self.operations = 'update'
                self.search_id = record.id
            elif not record and self.name and self.surname:
                record = self.env['res.partner'].search([('name', '=', self.name), ('surname', '=', self.surname)],
                                                        limit=1)
                if record:
                    self.operations = 'update'
                    self.search_id = record.id
                elif not record and self.name:
                    record = self.env['res.partner'].search([('name', '=', self.name)], limit=1)
                    if record:
                        self.operations = 'update'
                        self.search_id = record.id
                    else:
                        self.operations = 'create'
        elif not self.id_number and self.name and self.surname:
            record = self.env['res.partner'].search([('name', '=', self.name), ('surname', '=', self.surname)], limit=1)
            if record:
                self.operations = 'update'
                self.search_id = record.id
            elif not record and self.name:
                record = self.env['res.partner'].search([('name', '=', self.name)], limit=1)
                if record:
                    self.operations = 'update'
                    self.search_id = record.id
                else:
                    self.operations = 'create'
        elif not self.surname and not self.id_number and self.name:
            record = self.env['res.partner'].search([('name', '=', self.name)], limit=1)
            if record:
                self.operations = 'update'
                self.search_id = record.id
            else:
                self.operations = 'create'
        else:
            self.operations = 'create'

    def update_record(self):
        data = {
            'name': self.name,
            'surname': self.surname,
            'initials': self.initials,
            'dependent_code': self.dependent_code,
            'birth_date': self.dob,
            'id_number': self.id_number,
            'gender': self.gender.lower(),
        }
        self.search_id.update(data)

    def create_record(self):
        data = {
            'name': self.name,
            'surname': self.surname,
            'initials': self.initials,
            'dependent_code': self.dependent_code,
            'birth_date': self.dob,
            'id_number': self.id_number,
            'gender': self.gender.lower(),
            'customer': True
        }
        code = ['0','00']
        if self.dependent_code in code:
            parent_id = self.env['res.partner'].create(data)
            self.search_id = parent_id.id
            self.operations = 'update'
        else:
            parent_id = self.search([('msv_response_id','=',self.msv_response_id.id),('dependent_code','in',code)],limit=1)
            if parent_id.search_id:
                data.update({'parent_id':parent_id.search_id.id})
                self.env['res.partner'].create(data)
                self.operations = 'update'
            else:
                data1 = {
                    'name': parent_id.name,
                    'surname': parent_id.surname,
                    'initials': parent_id.initials,
                    'dependent_code': parent_id.dependent_code,
                    'birth_date': parent_id.dob,
                    'id_number': parent_id.id_number,
                    'gender': parent_id.gender.lower(),
                    'customer': True
                }
                id = self.env['res.partner'].create(data1)
                parent_id.search_id = id.id
                self.operations = 'update'
                data.update({'parent_id': id.id})
                self.env['res.partner'].create(data)

