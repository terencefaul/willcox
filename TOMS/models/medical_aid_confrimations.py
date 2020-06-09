from odoo import fields, models, api


class medical_aid_confrimations (models.Model):
    _name = 'humint.medical.aid.confrimations'
    _description = 'Medical Aid Confrimations'
    _rec_name = 'patient'

    name = fields.Char()
    patient = fields.Many2one('res.partner')
    account_no  = fields.Char(related="patient.individual_internal_ref", string="Account Number")
    patient_no = fields.Char(related="patient.patient_number",  string = "Patient Number")
    calendar_id = fields.Many2one('calendar.event', string="calendar")
    examination_id = fields.Many2one('clinical.examination', string="examination")
    medical_aid = fields.Many2one(related="patient.medical_aid_id")
    date = fields.Date(string='Date',required=False)
    period = fields.Selection([('3 Months', '3 Months'),
                              ('6 Months','6 Months'),
                              ('1 Year', '1 Year'),
                              ('18 Months', '18 Months'),
                              ('2 Years', '2 Years'),])
    overall_spectacle_limit = fields.Float()
    overall_limit = fields.Float()
    frame_limit = fields.Float()
    lens_limit = fields.Float()
    sv_limit = fields.Float()
    bf_limit = fields.Float()
    mf_limit = fields.Float()
    tints = fields.Boolean()
    coating = fields.Boolean()
    arc = fields.Boolean()
    contact_lens_limit = fields.Float()
    contact_lens_consult = fields.Float()
    eye_exam = fields.Float()
    tomometry = fields.Float()
    comments = fields.Text()
    spoke_to = fields.Char()
    staff_mem = fields.Many2one('res.users', default=lambda self:self._uid)



