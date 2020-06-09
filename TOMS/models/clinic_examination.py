import traceback

from datetime import date, datetime
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import Warning, ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta


class clinic_examination(models.Model):
    _name = 'clinical.examination'
    _description = 'Clinical Examination'

    @api.model
    def _lang_get(self):
        return self.env['res.lang'].get_installed()

    @api.model
    def default_get(self, fieldlist):
        res = super(clinic_examination, self).default_get(fieldlist)
        lst = []
        test_auto = self.env.ref('TOMS.clinical_test_auto')
        test_ret = self.env.ref('TOMS.clinical_test_ret')
        res.update(
            frontliner_id=self.env.user.id
        )
        test_subjective = self.env.ref('TOMS.clinical_test_subjective')
        if test_auto:
            lst.append((0, 0, {'name': test_auto.name, 'test_name': test_auto.name}))
        if test_ret:
            lst.append((0, 0, {'name': test_ret.name, 'test_name': test_ret.name}))
        if test_subjective:
            lst.append((0, 0, {'name': test_subjective.name, 'test_name': test_subjective.name}))
            res.update({'contact_clinical_test_ids': [
                (0, 0, {'name': test_subjective.name, 'test_name': test_subjective.name})]})
        res.update({'clinical_test_ids': lst})
        return res

    def _default_pricelist(self):
        return self.env['product.pricelist'].search([('currency_id', '=', self.env.user.company_id.currency_id.id)],
                                                    limit=1)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('examination_seq') or _('New')
        return super(clinic_examination, self).create(vals)

    def _get_tometry_selection(self):
        lst = []
        for each in range(1, 31):
            lst.append((str(each), str(each)))
        return lst

    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection([('new', 'New'), ('inprogress', 'In Progress'), ('done', 'Done'), ('cancel', 'Cancelled')],
                             default="new")
    name = fields.Char(string="Exam #")
    partner_id = fields.Many2one('res.partner', string="Name")
    account_number = fields.Char(string='Account_number', related="partner_id.individual_internal_ref")
    birth_date = fields.Date(string="Birthdate", related="partner_id.birth_date")
    occupation = fields.Many2one(string="Occupation", related="partner_id.occupation")
    age_at_exam = fields.Integer(string="Age at Exam", compute="age_at_examination")
    lang = fields.Selection(_lang_get, string='Language', default=lambda self: self.env.lang, related="partner_id.lang")
    exam_date = fields.Date(string="Exam Date", default=date.today())
    chief_complaints = fields.Text(string="Chief Complaints ")
    health = fields.Text(string="Health")
    specific_visual_requirements = fields.Text(string="Specific Visual Requirements")
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist", default=_default_pricelist)
    dispensing_pricelist_id = fields.Many2one('product.pricelist', string="Pricelist ", default=_default_pricelist)
    examination_line_ids = fields.One2many('clinical.examination.line', 'clinical_exam_id')
    dispensing_line_ids = fields.One2many('dispensing.examination.line', 'clinical_exam_id')
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency ", readonly=True,
                                  required=True)
    dispensing_currency_id = fields.Many2one("res.currency", related='dispensing_pricelist_id.currency_id',
                                             string="Currency", readonly=True, required=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='onchange')
    amount_tax = fields.Monetary(string='Taxes ', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    dispensing_amount_untaxed = fields.Monetary(string='Untaxed Amount ', store=True, readonly=True,
                                                compute='_amount_all_dispensing', track_visibility='onchange')
    dispensing_amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all_dispensing')
    dispensing_amount_total = fields.Monetary(string='Total ', store=True, readonly=True,
                                              compute='_amount_all_dispensing', track_visibility='always')
    invoice_id = fields.Many2one("account.invoice", string='Invoices', copy=False)
    invoice_count = fields.Integer(string="Invoices ", compute="get_invoice_count")
    exam_count = fields.Integer(string="Exams", compute="get_exam_count")
    job_count = fields.Integer(string="Jobs", compute="get_job_count")
    contact_count = fields.Integer(string="Contacts", compute="get_contact_count")
    clinical_habitual_ids = fields.One2many('clinical.habitual', 'clinical_examination_id', copy=True)
    contact_clinical_habitual_ids = fields.One2many('contact.clinical.habitual', 'clinical_examination_id', copy=True)
    clinical_final_rx_ids = fields.One2many('clinical.final.rx', 'final_rx_id', copy=True)
    clinical_final_rx_dis_ids = fields.One2many('clinical.final.rx', 'final_rx_dis_id', string="Fitting Details")
    clinical_contact_final_rx_ids = fields.One2many('clinical.final.rx.contact', 'final_rx_id', copy=True)
    clinical_contact_final_rx_dis_ids = fields.One2many('clinical.final.rx.contact', 'final_rx_dis_id',
                                                        string="Fitting Details(Contacts)")
    clinical_test_ids = fields.One2many('clinical.test', 'clinical_examination_id', store=True, copy=True)
    contact_clinical_test_ids = fields.One2many('contact.clinical.test', 'clinical_examination_id', store=True,
                                                copy=True)
    od_unaided_distance = fields.Char()
    os_unaided_distance = fields.Char()
    od_aided_distance = fields.Char()
    os_aided_distance = fields.Char()
    od_pd_distance = fields.Float(string="Distance")
    os_pd_distance = fields.Float()
    distance_horizontal = fields.Char()
    distance_vertical = fields.Char()
    near_horizontal = fields.Char()
    near_vertical = fields.Char()
    b_horizontal = fields.Float()
    b_vertical = fields.Float()
    note_block = fields.Text()
    note_block_test = fields.Text()
    occuler_od_tometry = fields.Selection(selection=_get_tometry_selection)
    occuler_os_tometry = fields.Selection(selection=_get_tometry_selection)
    occuler_od_pupils = fields.Boolean()
    occuler_os_pupils = fields.Boolean()
    occuler_od_equal = fields.Boolean()
    occuler_os_equal = fields.Boolean()
    occuler_od_round = fields.Boolean()
    occuler_os_round = fields.Boolean()
    occuler_od_consensual = fields.Boolean()
    occuler_os_consensual = fields.Boolean()
    occuler_od_direct = fields.Boolean()
    occuler_os_direct = fields.Boolean()
    occuler_npc = fields.Integer(string="NPC")
    anterior_notes = fields.Text()
    cd_ratios_1 = fields.Selection([('0.0', '0.0'),
                                    ('0.1', '0.1'),
                                    ('0.2', '0.2'),
                                    ('0.3', '0.3'),
                                    ('0.4', '0.4'),
                                    ('0.5', '0.5'),
                                    ('0.6', '0.6'),
                                    ('0.7', '0.7'),
                                    ('0.8', '0.8'),
                                    ('0.9', '0.9'),
                                    ('1.0', '1.0'),
                                    ], default="0.0")
    cd_ratios_2 = fields.Selection([('0.0', '0.0'),
                                    ('0.1', '0.1'),
                                    ('0.2', '0.2'),
                                    ('0.3', '0.3'),
                                    ('0.4', '0.4'),
                                    ('0.5', '0.5'),
                                    ('0.6', '0.6'),
                                    ('0.7', '0.7'),
                                    ('0.8', '0.8'),
                                    ('0.9', '0.9'),
                                    ('1.0', '1.0'),
                                    ], default="0.0")
    posterior_notes = fields.Text(string="Posterior Notes ")
    iol_clear_first = fields.Boolean()
    iol_clear_second = fields.Boolean()
    iol_ns_first = fields.Boolean()
    iol_ns_second = fields.Boolean()
    iol_capsular_first = fields.Boolean()
    iol_capsular_second = fields.Boolean()
    iol_notes = fields.Text()
    optometrist_id = fields.Many2one('res.users', string="Optometrist")
    previous_optometrist_id = fields.Many2one('res.users', string="Previous Optometrist", readonly=True)
    dispenser_id = fields.Many2one('res.users', string="Dispenser")
    frontliner_id = fields.Many2one('res.users', string="Frontliner")
    final_rx_subtotal = fields.Html('Final Rx Subtotal', compute="get_final_rx_total")
    repurchase = fields.Boolean(string="Repurchase", readonly=True)
    appointment_id = fields.Many2one('calendar.event')
    child_ids = fields.One2many('res.partner', 'parent_id', "Family Info", compute="_compute_contact")
    old_chief_complaints = fields.Text(compute="_compute_patient_history", string="Chief Complaint")
    old_cd_ratios_1 = fields.Selection([('0.0', '0.0'),
                                        ('0.1', '0.1'),
                                        ('0.2', '0.2'),
                                        ('0.3', '0.3'),
                                        ('0.4', '0.4'),
                                        ('0.5', '0.5'),
                                        ('0.6', '0.6'),
                                        ('0.7', '0.7'),
                                        ('0.8', '0.8'),
                                        ('0.9', '0.9'),
                                        ('1.0', '1.0'),
                                        ], default="0.0", compute="_compute_patient_history", string="CD Ratios 1")
    old_cd_ratios_2 = fields.Selection([('0.0', '0.0'),
                                        ('0.1', '0.1'),
                                        ('0.2', '0.2'),
                                        ('0.3', '0.3'),
                                        ('0.4', '0.4'),
                                        ('0.5', '0.5'),
                                        ('0.6', '0.6'),
                                        ('0.7', '0.7'),
                                        ('0.8', '0.8'),
                                        ('0.9', '0.9'),
                                        ('1.0', '1.0'),
                                        ], default="0.0", compute="_compute_patient_history", string="CD Ratios 2")
    old_posterior_notes = fields.Text(compute="_compute_patient_history", string="Posterior Note")
    old_iol_notes = fields.Text(compute="_compute_patient_history", string="Iol Note")
    diameter_r = fields.Char(string="Diameter R")
    diameter_l = fields.Char(string="Diameter L")
    base_curve_r = fields.Char()
    base_curve_l = fields.Char()
    over_fraction_r = fields.Char()
    over_fraction_l = fields.Char()
    axis_orientation_r = fields.Char()
    axis_orientation_l = fields.Char()
    movement_r = fields.Char()
    movement_l = fields.Char()
    sag_r = fields.Char()
    sag_l = fields.Char()
    landing_zone_r = fields.Char()
    landing_zone_l = fields.Char()
    notes_r = fields.Text()
    notes_l = fields.Text()
    # error might come if partner has no internal ref. need to fix this
    acc_no = fields.Char(string='Account No.', related='partner_id.individual_internal_ref')
    fundus_os = fields.Binary("Fundus Image OS", attachment=True, store=True, help='Upload your Fundus Image')
    fundus_od = fields.Binary("Fundus Image OD", attachment=True, store=True, help='Upload your Fundus Image')
    grab_a_heart = fields.Text()
    medical_aid_confirmation_ids = fields.One2many("humint.medical.aid.confrimations", 'examination_id')

    @api.onchange('clinical_test_ids')
    def onchange_clinical_test_ids(self):
        clinical_test = self.clinical_test_ids.filtered(lambda l: l.name == 'Subjective')
        contact_clinical_test = self.contact_clinical_test_ids.filtered(lambda l: l.name == 'Subjective')
        if clinical_test and contact_clinical_test:
            contact_clinical_test.od_syh = clinical_test.od_syh
            contact_clinical_test.od_cyl = clinical_test.od_cyl
            contact_clinical_test.od_axis = clinical_test.od_axis
            contact_clinical_test.od_add = clinical_test.od_add
            contact_clinical_test.od_va = clinical_test.od_va
            contact_clinical_test.os_syh = clinical_test.os_syh
            contact_clinical_test.os_cyl = clinical_test.os_cyl
            contact_clinical_test.os_axis = clinical_test.os_axis
            contact_clinical_test.os_add = clinical_test.os_add
            contact_clinical_test.os_va = clinical_test.os_va

    @api.multi
    @api.depends('partner_id')
    def _compute_patient_history(self):
        for each in self:
            if each.partner_id.id:
                domain = [('partner_id', '=', each.partner_id.id)]
                if each.id:
                    domain.append(('id', '!=', each.id))
                last_exam_rec = self.search(domain,
                                            order='id desc', limit=1)
                if last_exam_rec:
                    each.old_chief_complaints = last_exam_rec.chief_complaints
                    each.old_cd_ratios_1 = last_exam_rec.cd_ratios_1
                    each.old_cd_ratios_2 = last_exam_rec.cd_ratios_2
                    each.old_posterior_notes = last_exam_rec.posterior_notes
                    each.old_iol_notes = last_exam_rec.iol_notes

    @api.one
    @api.depends('partner_id')
    def _compute_contact(self):
        try:
            for rec in self:
                child_list = []
                if rec.partner_id and not rec.partner_id.parent_id:
                    child_list += rec.partner_id.child_ids.ids
                if rec.partner_id and rec.partner_id.parent_id:
                    child_list.append(rec.partner_id.parent_id.id)
                    child_ids = rec.partner_id.parent_id.child_ids.filtered(lambda l: l.id != rec.partner_id.id)
                    child_list += child_ids.ids
                if child_list:
                    for each in child_list:
                        if isinstance(each, int):
                            rec.child_ids = [(4, each)]
        except:
            traceback.print_exc()

    @api.multi
    def copy_check_box(self):
        self.occuler_os_pupils = self.occuler_od_pupils
        self.occuler_os_equal = self.occuler_od_equal
        self.occuler_os_round = self.occuler_od_round
        self.occuler_os_consensual = self.occuler_od_consensual
        self.occuler_os_direct = self.occuler_od_direct

    @api.multi
    def copy_iol_check_box(self):
        self.iol_clear_second = self.iol_clear_first
        self.iol_ns_second = self.iol_ns_first
        self.iol_capsular_second = self.iol_capsular_first

    @api.multi
    @api.depends('partner_id')
    def get_contact_count(self):
        if self.partner_id:
            rec_id = self.env['res.partner'].search_count([('parent_id', '=', self.partner_id.id)])
            self.contact_count = rec_id

    @api.multi
    def get_final_rx_total(self):
        final_rx_group_by = {}
        for each in self.dispensing_line_ids:
            for each_line in each:
                if each_line.clinical_final_rx_id:
                    name = each_line.clinical_final_rx_id.name.replace(' ', '')
                    if not name in final_rx_group_by:
                        final_rx_group_by[name] = {
                            'name': each_line.clinical_final_rx_id.name,
                            'total': each_line.price_subtotal,
                            'symbol': each_line.currency_id.symbol,
                            'position': each_line.currency_id.position
                        }
                    else:
                        final_rx_group_by[name]['total'] += each_line.price_subtotal
                if each_line.contact_clinical_final_rx_id:
                    name = each_line.contact_clinical_final_rx_id.name.replace(' ', '')
                    if not name in final_rx_group_by:
                        final_rx_group_by[name] = {
                            'name': each_line.contact_clinical_final_rx_id.name,
                            'total': each_line.price_subtotal,
                            'symbol': each_line.currency_id.symbol,
                            'position': each_line.currency_id.position
                        }
                    else:
                        final_rx_group_by[name]['total'] += each_line.price_subtotal
        html = """
        <table class='table table-striped' style='width:50%'>
            <thead>
                <tr>
                    <th>Clinical Final Rx</th>
                    <th>Subtotal Amount</th>
                </tr>
            </thead>
           """
        for key in sorted(final_rx_group_by):
            amount = str("{0:,.2f}".format(final_rx_group_by[key]['total']))
            if final_rx_group_by[key]['position'] == 'after':
                amount += " " + final_rx_group_by[key]['symbol']
            elif final_rx_group_by[key]['position'] == 'before':
                amount = final_rx_group_by[key]['symbol'] + " " + str(
                    "{0:,.2f}".format(final_rx_group_by[key]['total']))
            html += """
                    <tbody>
                     <tr>
                        <td>""" + final_rx_group_by[key]['name'] + """ </td>
                        <td>""" + amount + """</td>
                    </tr>"""
        html += """</tbody>
                </table>"""
        self.final_rx_subtotal = html

    @api.depends('invoice_id')
    def get_invoice_count(self):
        self.invoice_count = len(self.invoice_id)

    @api.multi
    @api.depends('partner_id')
    def get_job_count(self):
        if self.partner_id:
            rec_id = self.env['project.task'].search_count([('exam_id', '=', self.id)])
            self.job_count = rec_id

    @api.multi
    def examination_repurchase(self):
        record_id = self.copy()
        record_id.repurchase = True
        return {
            'name': 'Examination',
            'type': 'ir.actions.act_window',
            'res_model': 'clinical.examination',
            'view_type': 'form',
            'res_id': record_id.id,
            'view_mode': 'form',
        }

    @api.multi
    def examination_invoice(self):
        if not self.dispenser_id:
            self.dispenser_id = self.env.user.id
        inv_data = self._prepare_invoice()
        if self.examination_line_ids or self.dispensing_line_ids:
            invoice_id = self.env['account.invoice'].create(inv_data)
            if invoice_id:
                for each in self.examination_line_ids:
                    vals = self.prepare_invoice_lines(invoice_id, each, final_rx=False)
                    self.env['account.invoice.line'].create(vals)
                    invoice_id.compute_taxes()
                for each in self.dispensing_line_ids:
                    vals = self.prepare_invoice_lines(invoice_id, each, final_rx=True)
                    self.env['account.invoice.line'].create(vals)
                    invoice_id.compute_taxes()
                self.invoice_id = invoice_id.id
        else:
            raise ValidationError(_('Please create some invoice lines.'))

    @api.multi
    @api.depends('partner_id')
    def get_exam_count(self):
        if self.partner_id:
            rec_id = self.env['clinical.examination'].search_count(
                [('partner_id', '=', self.partner_id.id), ('active', '=', True)])
            self.exam_count = rec_id

    @api.multi
    def action_view_invoice(self):
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
        action['res_id'] = self.invoice_id.id
        return action

    @api.multi
    def prepare_invoice_lines(self, invoice_id, line, final_rx):
        self.ensure_one()
        res = {}
        account = line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (line.product_id.name, line.product_id.id, line.product_id.categ_id.name))
        if not line.icd_codes_ids:
            raise ValidationError(_('[%s] %s , does not have an ICD Code. Please assign an ICD code to continue.') % (
                line.product_id.default_code, line.product_id.name))
        res = {
            'name': line.product_id.name,
            'account_id': account.id,
            'price_unit': line.price_unit,
            'quantity': line.product_uom_qty,
            'discount': line.discount,
            'uom_id': line.product_id.uom_id.id,
            'invoice_id': invoice_id.id,
            'product_id': line.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, line.tax_id.ids)],
            'icd_codes_ids': [(6, 0, line.icd_codes_ids.ids)]
        }
        if final_rx:
            res.update({'final_rx_id': line.clinical_final_rx_id.id,
                        'contact_final_rx_id': line.contact_clinical_final_rx_id.id})
        return res

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        customer_id = False
        if self.partner_id.parent_id:
            customer_id = self.partner_id.parent_id.id
        else:
            customer_id = self.partner_id.id
        invoice_vals = {
            'name': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_id.property_account_receivable_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'company_id': self.env.user.company_id.id,
            'exam_date': self.exam_date,
            'optometrist_id': self.optometrist_id.id,
            'dispenser_id': self.dispenser_id.id,
            'frontliner_id': self.frontliner_id.id,
            'patient_id': self.partner_id.id,
            'partner_id': customer_id,
            'pricelist_id': self.pricelist_id.id,
            'payment_term_id':self.env['account.payment.term'].search([('name','=','Medical Aid to Pay')],limit=1).id
        }
        return invoice_vals

    @api.multi
    def open_patient_exam(self):
        return {
            'name': 'Examination',
            'type': 'ir.actions.act_window',
            'res_model': 'clinical.examination',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id), ('active', '=', True)]
        }

    @api.multi
    def action_open_job(self):
        return {
            'name': 'Jobs',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_type': 'form',
            'view_mode': 'kanban,form',
            'domain': [('exam_id', '=', self.id)]
        }

    @api.multi
    def action_contact_count(self):
        return {
            'name': 'Customer',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('customer', '=', True), ('parent_id', '=', self.partner_id.id)]
        }

    @api.constrains('clinical_habitual_ids')
    def check_clinical_habitual_ids(self):
        domain = [('partner_id', '=', self.partner_id.id), ('state', '=', 'done'), ('id', '!=', self.id)]
        res_id = self.env['clinical.examination'].search(domain, order="id desc", limit=1)
        last_clinical_test_id = res_id.clinical_test_ids.filtered(lambda l: l.name == 'Subjective')
        last_habitual_rec = self.clinical_habitual_ids.filtered(lambda l: l.is_subjective)
        if last_clinical_test_id and last_habitual_rec:
            if last_habitual_rec.name != last_clinical_test_id.name or \
                    last_habitual_rec.od_syh != last_clinical_test_id.od_syh or \
                    last_habitual_rec.od_cyl != last_clinical_test_id.od_cyl or \
                    last_habitual_rec.od_axis != last_clinical_test_id.od_axis or \
                    last_habitual_rec.od_prism != last_clinical_test_id.od_prism or \
                    last_habitual_rec.od_add != last_clinical_test_id.od_add or \
                    last_habitual_rec.od_va != last_clinical_test_id.od_va or \
                    last_habitual_rec.os_syh != last_clinical_test_id.os_syh or \
                    last_habitual_rec.os_cyl != last_clinical_test_id.os_cyl or \
                    last_habitual_rec.os_axis != last_clinical_test_id.os_axis or \
                    last_habitual_rec.os_prism != last_clinical_test_id.os_prism or \
                    last_habitual_rec.os_add != last_clinical_test_id.os_add or \
                    last_habitual_rec.os_va != last_clinical_test_id.os_va:
                raise ValidationError(_('You cannot change habitual subjective line.'))

    @api.depends('examination_line_ids.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.examination_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.depends('dispensing_line_ids.price_total')
    def _amount_all_dispensing(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.dispensing_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'dispensing_amount_untaxed': order.dispensing_pricelist_id.currency_id.round(amount_untaxed),
                'dispensing_amount_tax': order.dispensing_pricelist_id.currency_id.round(amount_tax),
                'dispensing_amount_total': amount_untaxed + amount_tax,
            })

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        exam_id = self.search([('partner_id.id', '=', self.partner_id.id)], order="id desc", limit=1)
        if exam_id:
            self.previous_optometrist_id = exam_id.optometrist_id.id
        else:
            self.previous_optometrist_id = False
        self.pricelist_id = False
        self.dispensing_pricelist_id = False
        self.exam_count = False
        self.contact_count = False
        self.job_count = False
        if self.partner_id:
            if self._origin:
                job_rec_id = self.env['project.task'].search_count(
                    [('exam_id', '=', self._origin.id), ('partner_id', '=', self.partner_id.id)])
                self.job_count = job_rec_id
            rec_id = self.search_count([('partner_id', '=', self.partner_id.id)])
            self.exam_count = rec_id
            contact_rec_id = self.env['res.partner'].search_count([('parent_id', '=', self.partner_id.id)])
            self.contact_count = contact_rec_id
            if self.partner_id.plan_option_id and self.partner_id.plan_option_id.pricelist_id:
                self.pricelist_id = self.partner_id.plan_option_id.pricelist_id.id
            elif self.partner_id.property_product_pricelist:
                self.pricelist_id = self.partner_id.property_product_pricelist.id

            if self.partner_id.plan_option_id and self.partner_id.plan_option_id.pricelist_id:
                self.dispensing_pricelist_id = self.partner_id.plan_option_id.pricelist_id.id
            elif self.partner_id.property_product_pricelist:
                self.dispensing_pricelist_id = self.partner_id.property_product_pricelist.id
            # if self.partner_id.option_id.code:
            # if self.partner_id.option_id.code == 'SAOA':
            # pricelist_id = self.env.ref('TOMS.product_pricelist_saoa')
            # elif self.partner_id.option_id.code == 'PPN1':
            # pricelist_id = self.env.ref('TOMS.product_pricelist_ppn1')

            # if pricelist_id:
            #     self.pricelist_id = pricelist_id.id
            #     self.dispensing_pricelist_id = pricelist_id.id

            self.ensure_one()
            domain = [('partner_id', '=', self.partner_id.id), ('state', '=', 'done')]
            if self.id:
                domain.append(('id', '!=', self.id))
            res_id = self.search(domain, order="id desc", limit=3)
            line_lst = []
            contact_line_list = []
            count = 1
            for each in res_id:
                if count == 1:
                    for each_line in each.clinical_test_ids:
                        if each_line.name == 'Subjective':
                            line_lst.append([0, 0, {
                                'name': each_line.name,
                                'od_syh': each_line.od_syh,
                                'od_cyl': each_line.od_cyl,
                                'od_axis': each_line.od_axis,
                                'od_prism': each_line.od_prism,
                                'od_add': each_line.od_add,
                                'od_va': each_line.od_va,
                                'os_syh': each_line.os_syh,
                                'os_cyl': each_line.os_cyl,
                                'os_axis': each_line.os_axis,
                                'os_prism': each_line.os_prism,
                                'os_add': each_line.os_add,
                                'os_va': each_line.os_va,
                                'is_subjective': True,
                                'date': each.create_date,
                            }])
                for each_line in each.clinical_contact_final_rx_ids:
                    if each_line.name == 'Trial Contact Lens':
                        contact_line_list.append([0, 0, {
                            'name': each_line.name,
                            'create_date': each_line.create_date,
                            'od_syh': each_line.od_syh,
                            'od_cyl': each_line.od_cyl,
                            'od_axis': each_line.od_axis,
                            'od_add': each_line.od_add,
                            'od_va': each_line.od_va,
                            'os_syh': each_line.os_syh,
                            'os_cyl': each_line.os_cyl,
                            'os_axis': each_line.os_axis,
                            'os_add': each_line.os_add,
                            'os_va': each_line.os_va,
                            'is_subjective': False,
                            'date': each.create_date,
                        }])
                    if each_line.name == 'Final Contact Lens' and count == 1:
                        contact_line_list.append([0, 0, {
                            'name': each_line.name,
                            'create_date': each_line.create_date,
                            'od_syh': each_line.od_syh,
                            'od_cyl': each_line.od_cyl,
                            'od_axis': each_line.od_axis,
                            'od_add': each_line.od_add,
                            'od_va': each_line.od_va,
                            'os_syh': each_line.os_syh,
                            'os_cyl': each_line.os_cyl,
                            'os_axis': each_line.os_axis,
                            'os_add': each_line.os_add,
                            'os_va': each_line.os_va,
                            'is_subjective': False,
                            'date': each.create_date,
                        }])
                count += 1
            self.clinical_habitual_ids = line_lst
            self.contact_clinical_habitual_ids = contact_line_list

    @api.multi
    @api.depends('birth_date')
    def age_at_examination(self):
        for each in self:
            if each.birth_date:
                birth_date = each.birth_date
                each.age_at_exam = date.today().year - birth_date.year

    @api.multi
    def progress_examination(self):
        self.state = 'inprogress'

    @api.multi
    def done_examination(self):
        self.state = 'done'
        self.partner_id.last_exam_date = self.exam_date
        recall_date = self.partner_id.last_exam_date
        self.partner_id.recall_exam_date = recall_date + relativedelta(months=18)

    @api.multi
    def cancel_examination(self):
        self.state = 'cancel'


class clinical_line_examination(models.Model):
    _name = 'clinical.examination.line'
    _description = 'Clinical Examination Line'

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=True)
    name = fields.Text(string='Description', required=True)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    clinical_exam_id = fields.Many2one('clinical.examination', string="Clinical Exam")
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    currency_id = fields.Many2one(related='clinical_exam_id.currency_id', store=True, string='Currency', readonly=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes ', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    icd_codes_ids = fields.Many2many('icd.codes', string="ICD10")

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, self.env.user.company_id.currency_id, line.product_uom_qty,
                                            product=line.product_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.multi
    @api.onchange('product_id', 'product_uom_qty')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}
        self.icd_codes_ids = self.product_id.common_icd_id
        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        product = self.product_id.with_context(
            partner=self.clinical_exam_id.partner_id.id,
            quantity=self.product_uom_qty,
            pricelist=self.clinical_exam_id.pricelist_id.id,
            uom=self.product_id.uom_id.id,
        )
        result = {'domain': domain}
        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result
        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name
        self._compute_tax_id()
        if self.clinical_exam_id.pricelist_id and self.clinical_exam_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id, self.tax_id, self.env.user.company_id)
        self.update(vals)
        return result

    @api.multi
    def _get_display_price(self, product):
        if self.clinical_exam_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.clinical_exam_id.pricelist_id.id).price
        final_price, rule_id = self.clinical_exam_id.pricelist_id.get_product_price_rule(self.product_id,
                                                                                         self.product_uom_qty or 1.0,
                                                                                         self.clinical_exam_id.partner_id)
        context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order)
        base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id, rule_id,
                                                                                              self.product_uom_qty,
                                                                                              self.product_uom,
                                                                                              self.order_id.pricelist_id.id)
        if currency_id != self.order_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(context_partner).compute(base_price,
                                                                                                            self.order_id.pricelist_id.currency_id)
        return max(base_price, final_price)

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            taxes = line.product_id.taxes_id
            line.tax_id = taxes


class dispensing_line_examination(models.Model):
    _name = 'dispensing.examination.line'
    _order = "clinical_final_rx_id"
    _description = 'Despensing Examination Line'

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=True)
    name = fields.Text(string='Description', required=True)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    clinical_exam_id = fields.Many2one('clinical.examination', string="Clinical Exam")
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    currency_id = fields.Many2one(related='clinical_exam_id.currency_id', store=True, string='Currency', readonly=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes ', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    clinical_final_rx_id = fields.Many2one('clinical.final.rx')
    contact_clinical_final_rx_id = fields.Many2one('clinical.final.rx.contact')
    display_final_rx_id = fields.Many2one('clinical.final.rx', string="Final Rx")
    final_rx_flage = fields.Boolean()
    icd_codes_ids = fields.Many2many('icd.codes', string="ICD10")
    vendor_id = fields.One2many(related='product_id.seller_ids')
    wizard_final_rx_contact_id  = fields.One2many('wizard.final.rx.contact','dispensing_examination_line_id')
    l_r =fields.Selection(related="wizard_final_rx_contact_id.l_r")

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, self.env.user.company_id.currency_id, line.product_uom_qty,
                                            product=line.product_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.multi
    def _get_display_price(self, product):
        if self.clinical_exam_id.dispensing_pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.clinical_exam_id.pricelist_id.id).price
        final_price, rule_id = self.clinical_exam_id.dispensing_pricelist_id.get_product_price_rule(self.product_id,
                                                                                                    self.product_uom_qty or 1.0,
                                                                                                    self.clinical_exam_id.partner_id)
        context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order)
        base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id, rule_id,
                                                                                              self.product_uom_qty,
                                                                                              self.product_uom,
                                                                                              self.order_id.pricelist_id.id)
        if currency_id != self.order_id.dispensing_pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(context_partner).compute(base_price,
                                                                                                            self.order_id.pricelist_id.currency_id)
        return max(base_price, final_price)

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            taxes = line.product_id.taxes_id
            line.tax_id = taxes


class clinical_habitual(models.Model):
    _name = 'clinical.habitual'
    _description = 'Clinical Habitual'

    name = fields.Char(string="Name")
    od_syh = fields.Float(string="Sph")
    od_cyl = fields.Float(string="Cyl")
    od_axis = fields.Integer(string="Axis")
    od_prism = fields.Char(string="Prism")
    od_add = fields.Float(string="Add")
    od_va = fields.Float(string="VA")
    os_syh = fields.Float(string="Sph ")
    os_cyl = fields.Float(string="Cyl ")
    os_axis = fields.Integer(string="Axis ")
    os_prism = fields.Char(string="Prism ")
    os_add = fields.Float(string="Add ")
    os_va = fields.Float(string="VA ")
    is_subjective = fields.Boolean(string="flag")
    clinical_examination_id = fields.Many2one('clinical.examination')
    date = fields.Datetime(string="Date")


    @api.one
    @api.constrains('od_axis','os_axis')
    def _check_value(self):
        if self.od_axis > 180 or self.od_axis < 0 or self.os_axis > 180 or self.os_axis <0:
            raise ValidationError(_('Habitual Axis value must be between 0 - 180'))


class clinical_final_rx(models.Model):
    _name = 'clinical.final.rx'
    _description = 'Clinical Final RX'

    @api.model
    def create(self, vals):
        res = super(clinical_final_rx, self).create(vals)
        if res.final_rx_id and res.dispense:
            rec = res.read()[0]
            rec.update({'final_rx_id': False, 'final_rx_dis_id': res.final_rx_id.id, 'old_id': res.id})
            self.create(rec)
        return res

    @api.multi
    def write(self, vals):
        res = super(clinical_final_rx, self).write(vals)
        for each in self:
            rec = self.search([('old_id', '=', each.id)])
            if each.dispense and not each.final_rx_dis_id:
                value = each.read()[0]
                value.update({'final_rx_id': False, 'final_rx_dis_id': each.final_rx_id.id, 'old_id': each.id})
                if rec:
                    rec.write(value)
                else:
                    rec.create(value)
            if not each.dispense:
                if rec:
                    rec.unlink()
        return res

    @api.one
    @api.constrains('od_axis','os_axis')
    def _check_value(self):
        if self.od_axis > 180 or self.od_axis < 0 or self.os_axis > 180 or self.os_axis <0:
            raise ValidationError(_('Final Rx Axis must be between 0 - 180'))



    name = fields.Char(string="Name")
    od_syh = fields.Float(string="Sph")
    od_cyl = fields.Float(string="Cyl")
    od_axis = fields.Integer(string="Axis")
    od_prism = fields.Char(string="Prism")
    od_add = fields.Float(string="Add")
    od_va = fields.Float(string="VA")
    os_syh = fields.Float(string="Sph ")
    os_cyl = fields.Float(string="Cyl ")
    os_axis = fields.Integer(string="Axis ")
    os_prism = fields.Char(string="Prism ")
    os_add = fields.Float(string="Add ")
    os_va = fields.Float(string="VA ")
    dispense = fields.Boolean(string="Dispense", default=True)
    final_rx_id = fields.Many2one('clinical.examination')
    final_rx_dis_id = fields.Many2one('clinical.examination')
    pupil_heights_r = fields.Float()
    pupil_heights_l = fields.Float()
    mono_r = fields.Float()
    mono_l = fields.Float()
    seg_heights_r = fields.Float()
    seg_heights_l = fields.Float()
    pd_r = fields.Float()
    pd_l = fields.Float()
    fitting_a = fields.Float()
    fitting_b = fields.Float()
    fitting_d = fields.Float()
    fitting_e = fields.Float()
    shape = fields.Float()
    instruction = fields.Text()
    clinical_final_rx_ids = fields.One2many('dispensing.examination.line', 'clinical_final_rx_id')
    task_id = fields.Many2one('project.task', copy=False)
    invoice_id = fields.Many2one(related="final_rx_dis_id.invoice_id")
    old_id = fields.Many2one('clinical.final.rx')

    lens_material = fields.Many2one('lens.material')
    lens_type_od = fields.Many2many('product.template', 'clinical_rx_product_lens_type_od',
                                    domain="[('categ_id.name','=','Lenses')]")
    lens_type_os = fields.Many2many('product.template', 'clinical_rx_product_lens_type_os',
                                    domain="[('categ_id.name','=','Lenses')]")
    addons_od = fields.Many2many('product.template', 'clinical_rx_product_addons_od',
                                 domain="[('categ_id.name','=','Addons')]")
    addons_os = fields.Many2many('product.template', 'clinical_rx_product_addons_os',
                                 domain="[('categ_id.name','=','Addons')]")
    frame_model = fields.Many2one('product.product', domain="[('categ_id.name','=','Frames')]",
                                  string="Frame Model")

    @api.onchange('od_prism','os_prism')
    def check_prism_values(self):
        if self.od_prism and not self.od_prism[0] in [str(x) for x in range(0,10)]:
            raise ValidationError(_('Make sure the first char has to be numeric for field "Prism".'))
        if self.os_prism and not self.os_prism[0] in [str(x) for x in range(0,10)]:
            raise ValidationError(_('Make sure the first char has to be numeric for field "Prism".'))

    # @api.multi
    # def read(self, fields=None, load='_classic_read'):
    #     print("\n \n res", fields)
    #     res = super(clinical_final_rx, self).read(fields=fields, load=load)
    #     if self.env.context.get('test_context') and ('dispense' in fields):
    #         res[:] = [d for d in res if d.get('dispense')]
    #         print("\n \n res", res)
    #     return res

    @api.multi
    def get_subjective_lines(self, each):
        subjective_line = {
            'od_syh': each.get('od_syh') if isinstance(each, dict) else each['od_syh'],
            'od_cyl': each.get('od_cyl') if isinstance(each, dict) else each['od_cyl'],
            'od_axis': each.get('od_axis') if isinstance(each, dict) else each['od_axis'],
            'od_prism': each.get('od_prism') if isinstance(each, dict) else each['od_prism'],
            'od_add': each.get('od_add') if isinstance(each, dict) else each['od_add'],
            'od_va': each.get('od_va') if isinstance(each, dict) else each['od_va'],
            'os_syh': each.get('os_syh') if isinstance(each, dict) else each['os_syh'],
            'os_cyl': each.get('os_cyl') if isinstance(each, dict) else each['os_cyl'],
            'os_axis': each.get('os_axis') if isinstance(each, dict) else each['os_axis'],
            'os_prism': each.get('os_prism') if isinstance(each, dict) else each['os_prism'],
            'os_add': each.get('os_add') if isinstance(each, dict) else each['os_add'],
            'os_va': each.get('os_va') if isinstance(each, dict) else each['os_va'],
        }
        return subjective_line

    @api.model
    def default_get(self, fieldlist):
        res = super(clinical_final_rx, self).default_get(fieldlist)
        if self._context.get('clinical_test_ids'):
            for each in self._context.get('clinical_test_ids')[-1:]:
                for each_line in each[-1:]:
                    if each_line:
                        res.update(self.get_subjective_lines(each_line))
                    else:
                        clinical_examination_id = self.env['clinical.examination'].browse(
                            self._context.get('record_id'))
                        for each in clinical_examination_id.clinical_test_ids.filtered(
                                lambda l: l.name == "Subjective"):
                            res.update(self.get_subjective_lines(each))
        return res

    @api.multi
    def add_fitting_details(self):
        product_fitting_detail = []
        for each in self.clinical_final_rx_ids:
            product_fitting_detail.append((0, 0, {
                'product_id': each.product_id.id,
                'name': each.name,
                'product_uom_qty': each.product_uom_qty,
                'price_unit': each.price_unit,
                'tax_id': [(6, 0, each.tax_id.ids)],
                'discount': each.discount,
                'price_subtotal': each.price_subtotal,
                'currency_id': each.currency_id.id,
                'final_rx_flage': each.final_rx_flage,
                'icd_codes_ids': [(6, 0, each.icd_codes_ids.ids)],
            }))
        return {
            'name': 'Fitting Details',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.final.rx',
            'view_id': self.env.ref('TOMS.final_rx_fitting_details_form').id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_clinical_final_rx_id': self.id,
                        'default_clinical_exam_id': self.final_rx_dis_id.id,
                        'default_pupil_heights_r': self.pupil_heights_r,
                        'default_pupil_heights_l': self.pupil_heights_l,
                        'default_mono_r': self.mono_r,
                        'default_mono_l': self.mono_l,
                        'default_seg_heights_r': self.seg_heights_r,
                        'default_seg_heights_l': self.seg_heights_l,
                        'default_pd_r': self.pd_r,
                        'default_pd_l': self.pd_l,
                        'default_fitting_a': self.fitting_a,
                        'default_fitting_b': self.fitting_b,
                        'default_fitting_d': self.fitting_d,
                        'default_fitting_e': self.fitting_e,
                        'default_shape': self.shape,
                        'default_instruction': self.instruction,
                        'default_wizard_final_rx_ids': product_fitting_detail,
                        'default_lens_material': self.lens_material.id,
                        'default_lens_type_od': [[6, 0, self.lens_type_od.ids]],
                        'default_lens_type_os': [[6, 0, self.lens_type_os.ids]],
                        'default_addons_od': [[6, 0, self.addons_od.ids]],
                        'default_addons_os': [[6, 0, self.addons_os.ids]],
                        'default_frame_model': self.frame_model.id
                        }
        }

    @api.multi
    def view_project_job(self):
        return {
            'name': 'Jobs',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_id': self.env.ref('project.view_task_form2').id,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.task_id.id
        }

    @api.multi
    def add_to_job_queue(self):
        purchase_order_line = []
        date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")[:10]
        final_rx_po_lines = self.clinical_final_rx_ids.filtered(lambda l: l.product_id.type == "consu")
        if final_rx_po_lines:
            seller_id = False
            if final_rx_po_lines[0].product_id.seller_ids:
                seller_id = final_rx_po_lines[0].product_id.seller_ids[0].name
            for each in final_rx_po_lines:
                if not each.product_id.seller_ids:
                    raise ValidationError(_('There is no supplier specified on products. Please review.'))
                lst = []
                for seller in each.product_id.seller_ids:
                    lst.append(seller.name.id)
                if seller_id.id not in lst:
                    raise ValidationError(_('Products selected are from different suppliers. Please review.'))
                seller = each.product_id._select_seller(
                    partner_id=seller_id,
                    quantity=each.product_uom_qty,
                    date=date,
                    uom_id=each.product_id.uom_po_id)
                date_planned = date
                if seller:
                    date_planned = self.env['purchase.order.line']._get_date_planned(seller).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT)
                purchase_order_line.append((0, 0, {
                    'product_id': each.product_id.id,
                    'name': each.name,
                    'product_qty': each.product_uom_qty,
                    'price_unit': seller.price,
                    'taxes_id': [(6, 0, each.product_id.supplier_taxes_id.ids)],
                    'product_uom': each.product_id.uom_po_id.id,
                    'currency_id': each.currency_id.id,
                    'date_planned': date_planned
                }))
            res = self.env['project.task'].create({
                'name': self.name,
                'partner_id': self.final_rx_dis_id.partner_id.id,
                'project_id': self.env.ref('TOMS.toms_company_jobs').id,
                'stage_id': self.env.ref('TOMS.stage_queued').id,
                'clinical_final_rx_id': self.id,
                'exam_id': self.final_rx_dis_id.id,
                'repurchase_job': self.final_rx_dis_id.repurchase,
            })
            if res:
                self.task_id = res.id
            self.env['purchase.order'].create({
                'date_order': datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                'partner_ref': self.final_rx_dis_id.name + ":" + self.name,
                'clinical_exam_id': self.final_rx_dis_id.id,
                'final_rx_id': self.id,
                'project_task_id': res.id,
                'partner_id': seller_id.id,
                'order_line': purchase_order_line,
            })


class clinical_test(models.Model):
    _name = 'clinical.test'
    _description = 'Clinical Test'

    name = fields.Char(string="Name", store=True)
    test_name = fields.Char(related='name', string="Name ")
    od_syh = fields.Float(string="Sph")
    od_cyl = fields.Float(string="Cyl")
    od_axis = fields.Integer(string="Axis")
    od_prism = fields.Char(string="Prism")
    od_add = fields.Float(string="Add")
    od_va = fields.Float(string="VA")
    os_syh = fields.Float(string="Sph ")
    os_cyl = fields.Float(string="Cyl ")
    os_axis = fields.Integer(string="Axis ")
    os_prism = fields.Char(string="Prism ")
    os_add = fields.Float(string="Add ")
    os_va = fields.Float(string="VA ")
    clinical_examination_id = fields.Many2one('clinical.examination')

    @api.one
    @api.constrains('od_axis','os_axis')
    def _check_value(self):
        if self.od_axis > 180 or self.od_axis < 0 or self.os_axis > 180 or self.os_axis <0:
            raise ValidationError(_('Axis value for test must be between 0 - 180'))


class wizard_final_rx(models.TransientModel):
    _name = 'wizard.final.rx'
    _description = 'Wizard Final RX'

    clinical_final_rx_id = fields.Many2one('clinical.final.rx')
    clinical_exam_id = fields.Many2one('clinical.examination')
    invoice_id = fields.Many2one(related="clinical_exam_id.invoice_id")
    pupil_heights_r = fields.Float()
    pupil_heights_l = fields.Float()
    mono_r = fields.Float()
    mono_l = fields.Float()
    seg_heights_r = fields.Float()
    seg_heights_l = fields.Float()
    pd_r = fields.Float(related="clinical_exam_id.od_pd_distance")
    pd_l = fields.Float(related="clinical_exam_id.os_pd_distance")
    fitting_a = fields.Float()
    fitting_b = fields.Float()
    fitting_d = fields.Float()
    fitting_e = fields.Float()
    shape = fields.Float()
    instruction = fields.Text()
    name = fields.Char(string="Name", related="clinical_final_rx_id.name")
    od_syh = fields.Float(string="Sph", related="clinical_final_rx_id.od_syh")
    od_cyl = fields.Float(string="Cyl", related="clinical_final_rx_id.od_cyl")
    od_axis = fields.Integer(string="Axis", related="clinical_final_rx_id.od_axis")
    od_prism = fields.Char(string="Prism", related="clinical_final_rx_id.od_prism")
    od_add = fields.Float(string="Add", related="clinical_final_rx_id.od_add")
    od_va = fields.Float(string="VA", related="clinical_final_rx_id.od_va")
    os_syh = fields.Float(string="Sph ", related="clinical_final_rx_id.os_syh")
    os_cyl = fields.Float(string="Cyl ", related="clinical_final_rx_id.os_cyl")
    os_axis = fields.Integer(string="Axis ", related="clinical_final_rx_id.os_axis")
    os_prism = fields.Char(string="Prism ", related="clinical_final_rx_id.os_prism")
    os_add = fields.Float(string="Add ", related="clinical_final_rx_id.os_add")
    os_va = fields.Float(string="VA ", related="clinical_final_rx_id.os_va")
    wizard_final_rx_ids = fields.One2many('wizard.final.rx.line', 'final_rx_id')
    pricelist_id = fields.Many2one('product.pricelist', related="clinical_exam_id.dispensing_pricelist_id",
                                   string=" Pricelist")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency ", readonly=True,
                                  required=True)
    repurchase = fields.Boolean(related="clinical_final_rx_id.final_rx_id.repurchase")

    lens_material = fields.Many2one('lens.material')
    lens_type_od = fields.Many2many( 'product.template', 'product_lens_type_od',
                                    domain="[('categ_id.name','=','Lenses'),('lens_material_id','=',lens_material)]", string="Lens Type OD")
    lens_type_os = fields.Many2many('product.template', 'product_lens_type_os',
                                    domain="[('categ_id.name','=','Lenses'),('lens_material_id','=',lens_material)]", string="Lens Type OS")
    addons_od = fields.Many2many('product.template', 'product_addons_od',
                                 domain="[('categ_id.name','=','Addons'),('lens_material_id','=',lens_material)]", string="Addons OD")
    addons_os = fields.Many2many('product.template', 'product_addons_os',
                                 domain="[('categ_id.name','=','Addons'),('lens_material_id','=',lens_material)]", string="Addons OS")
    frame_model = fields.Many2one('product.template', domain="[('categ_id.name','=','Frames')]",
                                  string="Frame Model")
    readonly_checkbox = fields.Boolean(string="Readonly Checkbox", default=True)
    own_frame = fields.Boolean(string='Own Frame', required=False)
    lens_select_od = fields.Boolean(default=True)
    lens_select_os = fields.Boolean(default=True)

    @api.constrains('lens_type_od')
    def check_lens_type_od_constrains(self):
        if not self.lens_type_od or len(self.lens_type_od) != 2:
            raise ValidationError(_('Please select 2 Lens Type Od.'))

    @api.constrains('lens_type_os')
    def check_lens_type_os_constrains(self):
        if not self.lens_type_os or len(self.lens_type_os) != 2:
            raise ValidationError(_('Please select 2 Lens Type Os.'))

    @api.multi
    def get_icd_codes(self, code):
        icd_code_id = self.env['icd.codes'].search([('code', '=', code)], limit=1)
        return icd_code_id

    @api.multi
    def fitting_details_apply(self):
        product_list = []
        final_rx_id = self.env['clinical.final.rx'].browse(self._context.get('default_clinical_final_rx_id'))
        codes_lst = []
        if final_rx_id.od_syh > 0 and final_rx_id.os_syh > 0:
            icd_code_id = self.get_icd_codes('H52.0')
            if icd_code_id:
                codes_lst.append(icd_code_id.id)
        if final_rx_id.od_syh < 0 and final_rx_id.os_syh < 0:
            icd_code_id = self.get_icd_codes('H52.1')
            if icd_code_id:
                codes_lst.append(icd_code_id.id)

        if final_rx_id.od_syh > 0 and final_rx_id.os_syh < 0 or final_rx_id.od_syh < 0 and final_rx_id.os_syh > 0:
            icd_code_ids = self.env['icd.codes'].search([('code', 'in', ['H52.3', 'H52.0', 'H52.1'])])
            for each in icd_code_ids:
                codes_lst.append(each.id)

        if final_rx_id.od_add > 0 and final_rx_id.os_add > 0:
            icd_code_id = self.get_icd_codes('H52.4')
            if icd_code_id:
                codes_lst.append(icd_code_id.id)

        if final_rx_id.od_cyl < 0 and final_rx_id.os_cyl < 0:
            icd_code_id = self.get_icd_codes('H52.2')
            if icd_code_id:
                codes_lst.insert(0, icd_code_id.id)
                if final_rx_id.od_cyl > 0 and final_rx_id.os_cyl > 0:
                    codes_lst.append(icd_code_id.id)
                else:
                    codes_lst.append(icd_code_id.id)
        for lens_type_od in self.lens_type_od:
            product_list.append((0, 0, {
                'product_id': lens_type_od.id,
                'name': lens_type_od.display_name,
                'price_unit': lens_type_od.list_price,
                'tax_id': [(6, 0, lens_type_od.taxes_id.ids)],
                'icd_codes_ids': [(6, 0, (codes_lst))]
            }))
        for lens_type_os in self.lens_type_os:
            product_list.append((0, 0, {
                'product_id': lens_type_os.id,
                'name': lens_type_os.display_name,
                'price_unit': lens_type_os.list_price,
                'tax_id': [(6, 0, lens_type_os.taxes_id.ids)],
                'icd_codes_ids': [(6, 0, (codes_lst))]
            }))
        for addons_od in self.addons_od:
            product_list.append((0, 0, {
                'product_id': addons_od.id,
                'name': addons_od.display_name,
                'price_unit': addons_od.list_price,
                'tax_id': [(6, 0, addons_od.taxes_id.ids)],
                'icd_codes_ids': [(6, 0, (codes_lst))]
            }))
        for addons_os in self.addons_os:
            product_list.append((0, 0, {
                'product_id': addons_os.id,
                'name': addons_os.display_name,
                'price_unit': addons_os.list_price,
                'tax_id': [(6, 0, addons_os.taxes_id.ids)],
                'icd_codes_ids': [(6, 0, (codes_lst))]
            }))
        if self.frame_model:
            product_list.append((0, 0, {
                'product_id': self.frame_model.id,
                'name': self.frame_model.display_name,
                'price_unit': self.frame_model.list_price,
                'tax_id': [(6, 0, self.frame_model.taxes_id.ids)],
                'icd_codes_ids': [(6, 0, (codes_lst))]
            }))
        self.wizard_final_rx_ids = False
        self.wizard_final_rx_ids = product_list
        self.readonly_checkbox = False
        return {
            'name': 'Fitting Details',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.final.rx',
            'view_id': self.env.ref('TOMS.final_rx_fitting_details_form').id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {'default_clinical_final_rx_id': final_rx_id.id, 'fitting_details_apply': True}
        }

    @api.multi
    def submit_fitting_details(self):
        if self.clinical_final_rx_id:
            self.clinical_final_rx_id.write({'pupil_heights_r': self.pupil_heights_r,
                                             'pupil_heights_l': self.pupil_heights_l,
                                             'mono_r': self.mono_r,
                                             'mono_l': self.mono_l,
                                             'seg_heights_r': self.seg_heights_r,
                                             'seg_heights_l': self.seg_heights_l,
                                             'pd_r': self.pd_r,
                                             'pd_l': self.pd_l,
                                             'fitting_a': self.fitting_a,
                                             'fitting_b': self.fitting_b,
                                             'fitting_d': self.fitting_d,
                                             'fitting_e': self.fitting_e,
                                             'shape': self.shape,
                                             'instruction': self.instruction,
                                             'lens_material': self.lens_material.id,
                                             'lens_type_od': [[6, 0, self.lens_type_od.ids]],
                                             'lens_type_os': [[6, 0, self.lens_type_os.ids]],
                                             'addons_od': [[6, 0, self.addons_od.ids]],
                                             'addons_os': [[6, 0, self.addons_os.ids]],
                                             'frame_model': self.frame_model.id,
                                             })

        final_rx_rec = self.wizard_final_rx_ids.filtered(lambda l: l.final_rx_flage != True)
        if final_rx_rec:
            self.clinical_exam_id.dispensing_line_ids.filtered(
                lambda l: l.clinical_final_rx_id.id == self.clinical_final_rx_id.id).unlink()
        self.readonly_checkbox = True
        for each in final_rx_rec:
            self.clinical_exam_id.write({'dispensing_line_ids': [(0, 0, {
                'clinical_final_rx_id': self.clinical_final_rx_id.id,
                'product_id': each.product_id.id,
                'name': each.name,
                'product_uom_qty': each.product_uom_qty,
                'price_unit': each.price_unit,
                'discount': each.discount,
                'tax_id': [(6, 0, each.tax_id.ids)],
                'icd_codes_ids': [(6, 0, each.icd_codes_ids.ids)],
                'final_rx_flage': True
            })]})


class wizard_final_rx_line(models.TransientModel):
    _name = 'wizard.final.rx.line'
    _description = 'Wizard Final RX Line'

    final_rx_id = fields.Many2one('wizard.final.rx', string="Final Rx")
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', store=True)
    name = fields.Text(string='Description', store=True)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    currency_id = fields.Many2one(related='final_rx_id.currency_id', store=True, string='Currency', readonly=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes ', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    wizard_final_rx_id = fields.Many2one('wizard.final.rx')
    icd_codes_ids = fields.Many2many('icd.codes', string="ICD10")
    final_rx_flage = fields.Boolean()

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, self.env.user.company_id.currency_id, line.product_uom_qty,
                                            product=line.product_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.multi
    def get_icd_codes(self, code):
        icd_code_id = self.env['icd.codes'].search([('code', '=', code)], limit=1)
        return icd_code_id

    @api.multi
    @api.onchange('product_id', 'product_uom_qty')
    def product_id_change(self):
        final_rx_id = self.env['clinical.final.rx'].browse(self._context.get('default_clinical_final_rx_id'))
        codes_lst = []
        if final_rx_id.od_syh > 0 and final_rx_id.os_syh > 0:
            icd_code_id = self.get_icd_codes('H52.0')
            if icd_code_id:
                codes_lst.append(icd_code_id.id)
        if final_rx_id.od_syh < 0 and final_rx_id.os_syh < 0:
            icd_code_id = self.get_icd_codes('H52.1')
            if icd_code_id:
                codes_lst.append(icd_code_id.id)

        if final_rx_id.od_syh > 0 and final_rx_id.os_syh < 0 or final_rx_id.od_syh < 0 and final_rx_id.os_syh > 0:
            icd_code_ids = self.env['icd.codes'].search([('code', 'in', ['H52.3', 'H52.0', 'H52.1'])])
            for each in icd_code_ids:
                codes_lst.append(each.id)

        if final_rx_id.od_add > 0 and final_rx_id.os_add > 0:
            icd_code_id = self.get_icd_codes('H52.4')
            if icd_code_id:
                codes_lst.insert(0, icd_code_id.id)

        if final_rx_id.od_cyl < 0 and final_rx_id.os_cyl < 0:
            icd_code_id = self.get_icd_codes('H52.2')
            if icd_code_id:
                codes_lst.insert(0, icd_code_id.id)
                if final_rx_id.od_cyl > 0 and final_rx_id.os_cyl > 0:
                    #                     codes_lst.append(icd_code_id.id)
                    codes_lst.insert(1, icd_code_id.id)
                else:
                    codes_lst.insert(0, icd_code_id.id)
        if self.product_id.common_icd_id:
            codes_lst.append(self.product_id.common_icd_id.id)
        self.icd_codes_ids = [(6, 0, (codes_lst))]

        if not self.product_id:
            return {'domain': {'product_uom': []}}
        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        product = self.product_id.with_context(
            partner=self.final_rx_id.clinical_exam_id.partner_id.id,
            quantity=self.product_uom_qty,
            pricelist=self.final_rx_id.pricelist_id.id,
            uom=self.product_id.uom_id.id,
        )
        result = {'domain': domain}
        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result
        #
        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()
        if self.final_rx_id.pricelist_id and self.final_rx_id.clinical_exam_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id, self.tax_id, self.env.user.company_id)
        self.update(vals)
        return result

    #
    @api.multi
    def _get_display_price(self, product):
        if self.final_rx_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.final_rx_id.pricelist_id.id).price
        final_price, rule_id = self.final_rx_id.pricelist_id.get_product_price_rule(self.product_id,
                                                                                    self.product_uom_qty or 1.0,
                                                                                    self.final_rx_id.clinical_exam_id.partner_id)
        context_partner = dict(self.env.context, partner_id=self.final_rx_id.clinical_exam_id.partner_id.id, date=None)
        base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id, rule_id,
                                                                                              self.product_uom_qty,
                                                                                              self.product_uom,
                                                                                              self.final_rx_id.pricelist_id.id)
        if currency_id != self.final_rx_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(context_partner).compute(base_price,
                                                                                                            self.final_rx_id.pricelist_id.currency_id)
        return max(base_price, final_price)

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            taxes = line.product_id.taxes_id
            line.tax_id = taxes
            if not line.product_id.taxes_id:
                confige_id = self.env['res.config.settings'].search([], limit=1, order="id desc")
                line.tax_id = confige_id.sale_tax_id

    @api.model
    def create(self, vals_list):
        print("\n\n\n\n self------", vals_list, self._context)
        res = super(wizard_final_rx_line, self).create(vals_list=vals_list)
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
