#################################################################################

from odoo import models,fields,api ,_

class ResponseWizard(models.Model):
    _name="response.error.wizard"
    _description="To view the information of the response payload"

    name = fields.Text(readonly=1,string="Status")
    response_error = fields.Char(string="Response Error")
    date_of_submission = fields.Date(string="Date Of Submission")
    Medical_aid = fields.Char(string="Medical Aid")
    practise_name = fields.Char(string="Practise Name")
    practise_number = fields.Char(string="Practise No")
    patient_name = fields.Many2one('res.partner',string="Patient Name")
    patient_dob = fields.Date(string="DOB")
    invoice_id = fields.Many2one("account.invoice",string="Invoice No")
    account_no = fields.Char(string="Account No")
    member_no = fields.Char(string="Member No")
    claim_status_lines_ids = fields.One2many("claim.status.lines",'response_id')


class ClaimStatusLines(models.Model):
    _name='claim.status.lines'
    _description="To store the invoice line with updated status"

    product_id = fields.Many2one('product.product',string="Product")
    quantity = fields.Float(string="Quantity")
    price_unit = fields.Float(string="Price")
    approved_amount = fields.Float(string="Approved")
    balance_amount = fields.Float(string="Balance")
    tax_ids = fields.Many2many("account.tax",string="Taxes")
    price_subtotal = fields.Float(string="Subtotal")
    status=fields.Char(string="status")
    response_id = fields.Many2one("response.error.wizard")
    reversal_id = fields.Many2one("response.reversal.wizard")

class ResponseWizard(models.Model):
    _name="response.reversal.wizard"
    _description="To view the information of fetch operations response payload"

    name = fields.Text(readonly=1,string="Status")
    response_error = fields.Char(string="Response Error")
    date_of_submission = fields.Date(string="Date Of Submission")
    Medical_aid = fields.Char(string="Medical Aid")
    practise_name = fields.Char(string="Practise Name")
    practise_number = fields.Char(string="Practise No")
    patient_name = fields.Many2one('res.partner',string="Patient Name")
    patient_dob = fields.Date(string="DOB")
    invoice_id = fields.Many2one("account.invoice",string="Invoice No")
    account_no = fields.Char(string="Account No")
    member_no = fields.Char(string="Member No")
    claim_status_reversal_lines_ids = fields.One2many("claim.status.lines",'reversal_id')




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

