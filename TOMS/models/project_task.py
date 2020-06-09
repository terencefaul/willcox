from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import Warning, ValidationError
from odoo.addons import decimal_precision as dp


class project_task(models.Model):
    _inherit = 'project.task'

    job_number = fields.Char()
    job_type = fields.Selection([('spectacles', 'Spectacles'), ('contact_lenses', 'Contact Lenses')], string="Job Type",
                                default="spectacles")
    mobile = fields.Char(string="Mobile", related="partner_id.mobile")
    work_phone = fields.Char(string="Work Phone", related="partner_id.work_phone")
    phone = fields.Char(string="Phone", related="partner_id.phone")
    email = fields.Char(related="partner_id.email", string="Email ")
    physical_location = fields.Many2one('stock.location', string="Physical Location")
    tray = fields.Char(string="Tray")
    examination_id = fields.Many2one('clinical.examination', string="Exam")
    exam_id = fields.Many2one('clinical.examination', string="Exam ")
    clinical_final_rx_id = fields.Many2one('clinical.final.rx')
    contact_clinical_final_rx_id = fields.Many2one('clinical.final.rx.contact')

    pupil_heights_r = fields.Float(related="clinical_final_rx_id.pupil_heights_r", readonly=True)
    pupil_heights_l = fields.Float(related="clinical_final_rx_id.pupil_heights_l", readonly=True)
    mono_r = fields.Float(related="clinical_final_rx_id.mono_r", readonly=True)
    mono_l = fields.Float(related="clinical_final_rx_id.mono_l", readonly=True)
    seg_heights_r = fields.Float(related="clinical_final_rx_id.seg_heights_r", readonly=True)
    seg_heights_l = fields.Float(related="clinical_final_rx_id.seg_heights_l", readonly=True)
    pd_r = fields.Float(related="clinical_final_rx_id.pd_r", readonly=True)
    pd_l = fields.Float(related="clinical_final_rx_id.pd_l", readonly=True)
    fitting_a = fields.Float(related="clinical_final_rx_id.fitting_a", readonly=True)
    fitting_b = fields.Float(related="clinical_final_rx_id.fitting_b", readonly=True)
    fitting_d = fields.Float(related="clinical_final_rx_id.fitting_d", readonly=True)
    fitting_e = fields.Float(related="clinical_final_rx_id.fitting_e", readonly=True)
    shape = fields.Float(related="clinical_final_rx_id.shape", readonly=True)
    instruction = fields.Text(related="clinical_final_rx_id.instruction", readonly=True)
    final_rx_name = fields.Char(string="Name", related="clinical_final_rx_id.name")
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

#    contact_final_rx_name = fields.Selection([('Trial Contact Lens', 'Trial Contact Lens'),
#                                              ('Final Contact Lens', 'Final Contact Lens')], string="Contact Name",
#                                             related="contact_clinical_final_rx_id.name")
    contact_final_rx_name = fields.Char(string='Decription', related="contact_clinical_final_rx_id.name")
    contact_od_syh = fields.Float(string="Contact Sph", related="contact_clinical_final_rx_id.od_syh")
    contact_od_cyl = fields.Float(string="Contact Cyl", related="contact_clinical_final_rx_id.od_cyl")
    contact_od_axis = fields.Integer(string="Contact Axis", related="contact_clinical_final_rx_id.od_axis")
    contact_od_add = fields.Float(string="Contact Add", related="contact_clinical_final_rx_id.od_add")
    contact_od_va = fields.Float(string="Contact VA", related="contact_clinical_final_rx_id.od_va")
    contact_os_syh = fields.Float(string="Contact Sph ", related="contact_clinical_final_rx_id.os_syh")
    contact_os_cyl = fields.Float(string="Contact Cyl ", related="contact_clinical_final_rx_id.os_cyl")
    contact_os_axis = fields.Integer(string="Contact Axis ", related="contact_clinical_final_rx_id.os_axis")
    contact_os_add = fields.Float(string="Contact Add ", related="contact_clinical_final_rx_id.os_add")
    contact_os_va = fields.Float(string="Contact VA ", related="contact_clinical_final_rx_id.os_va")

    contact_diameter_r = fields.Char(string="Diameter R", related="contact_clinical_final_rx_id.diameter_r")
    contact_diameter_l = fields.Char(string="Diameter L", related="contact_clinical_final_rx_id.diameter_l")
    contact_base_curve_r = fields.Char(related="contact_clinical_final_rx_id.base_curve_r")
    contact_base_curve_l = fields.Char(related="contact_clinical_final_rx_id.base_curve_l")
    contact_over_fraction_r = fields.Char(related="contact_clinical_final_rx_id.over_fraction_r")
    contact_over_fraction_l = fields.Char(related="contact_clinical_final_rx_id.over_fraction_l")
    contact_axis_orientation_r = fields.Char(related="contact_clinical_final_rx_id.axis_orientation_r")
    contact_axis_orientation_l = fields.Char(related="contact_clinical_final_rx_id.axis_orientation_l")
    contact_movement_r = fields.Char(related="contact_clinical_final_rx_id.movement_r")
    contact_movement_l = fields.Char(related="contact_clinical_final_rx_id.movement_l")
    contact_sag_r = fields.Char(related="contact_clinical_final_rx_id.sag_r")
    contact_sag_l = fields.Char(related="contact_clinical_final_rx_id.sag_l")
    contact_landing_zone_r = fields.Char(related="contact_clinical_final_rx_id.landing_zone_r")
    contact_landing_zone_l = fields.Char(related="contact_clinical_final_rx_id.landing_zone_l")
    contact_notes_r = fields.Text(related="contact_clinical_final_rx_id.notes_r")
    contact_notes_l = fields.Text(related="contact_clinical_final_rx_id.notes_l")

    project_task_ids = fields.One2many('project.product.line', 'project_task_id')
    is_contact_lense_job = fields.Boolean(string="Contact Lens Job")
    repurchase_job = fields.Boolean(string="Repurchase")
    exam_date = fields.Date(related="exam_id.exam_date")

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_lst = []
        stage_lst.append(self.env.ref('TOMS.stage_queued').id)
        stage_lst.append(self.env.ref('TOMS.stage_inprogress').id)
        stage_lst.append(self.env.ref('TOMS.stage_complete').id)
        stage_lst.append(self.env.ref('TOMS.stage_customer_collection').id)
        search_domain = [('id', 'in', stage_lst), ('active', '=', True)]
        if 'default_project_id' in self.env.context:
            search_domain = ['|', ('project_ids', '=', self.env.context['default_project_id'])] + search_domain
        stage_ids = self.env['project.task.type'].search([('active', '=', True), ('id', 'in', stage_lst)])
        stage_ids = self.env['project.task.type']._search(search_domain, access_rights_uid=SUPERUSER_ID)
        return self.env['project.task.type'].browse(stage_ids)

    @api.multi
    def project_fitting_details(self):
        product_fitting_detail = []
        for each in self.clinical_final_rx_id.clinical_final_rx_ids:
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
            'name': 'Examination',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_id': self.env.ref('TOMS.project_fitting_details_form').id,
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_clinical_final_rx_id': self.clinical_final_rx_id.id,
                        'default_project_task_ids': product_fitting_detail
                        },
            'target': 'new'
        }

    @api.multi
    def project_contact_fitting_details(self):
        product_fitting_detail = []
        for each in self.contact_clinical_final_rx_id.clinical_final_rx_ids:
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
            'name': 'Examination',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_id': self.env.ref('TOMS.project_contact_fitting_details_form').id,
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_contact_clinical_final_rx_id': self.contact_clinical_final_rx_id.id,
                        'default_project_task_ids': product_fitting_detail
                        },
            'target': 'new'
        }

    @api.multi
    def _track_template(self, tracking):
        res = super(project_task, self)._track_template(tracking)
        if self.stage_id.sms_template_id and self.stage_id.sms_template_id.from_mobile_verified_id and self.mobile:
            sms_compose = self.env['sms.compose'].create({
                'sms_template_id': self.stage_id.sms_template_id.id,
                'from_mobile_id': self.stage_id.sms_template_id.from_mobile_verified_id.id,
                'to_number': self.mobile,
                'sms_content': self.stage_id.sms_template_id.template_body,
                'media_id': self.stage_id.sms_template_id.media_id,
                'model': self._name,
                'record_id': self.id
            })
            if sms_compose:
                sms_compose.send_entity()
        return res

    @api.multi
    def open_job_exams(self):
        return {
            'name': 'Examination',
            'type': 'ir.actions.act_window',
            'res_model': 'clinical.examination',
            'view_id': self.env.ref('TOMS.clinical_examination_form_view').id,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.examination_id.id
        }

    @api.model
    def create(self, vals):
        res = super(project_task, self).create(vals)
        res.job_number = self.env['ir.sequence'].next_by_code('job_sequence')
        return res

    @api.multi
    def send_sms(self):
        model_id = self.env['ir.model'].search([('model', '=', self._name)])
        job_sms_template_id = self.env['sms.template'].search([('model_id', '=', model_id.id)])
        if model_id:
            return {
                'name': 'SMS Compose',
                'type': 'ir.actions.act_window',
                'res_model': 'sms.compose',
                'view_id': self.env.ref('sms_frame.sms_compose_view_form').id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {'default_to_number': self.mobile,
                            'default_model': self._name,
                            'default_record_id': self.id
                            }
            }


class project_task_type(models.Model):
    _inherit = 'project.task.type'

    sms_template_id = fields.Many2one('sms.template')
    active = fields.Boolean(string="active", default=True)


class project_product_line(models.Model):
    _name = 'project.product.line'
    _description = 'Prodcu Line'

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=True)
    name = fields.Text(string='Description', required=True)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes ',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    price_subtotal = fields.Monetary(string='Subtotal', readonly=True, store=True)
    clinical_exam_id = fields.Many2one('clinical.examination', string="Clinical Exam")
    currency_id = fields.Many2one(related='clinical_exam_id.currency_id', store=True, string='Currency', readonly=True)
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    price_tax = fields.Float(string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(string='Total', readonly=True, store=True)
    project_task_id = fields.Many2one('project.task')
    icd_codes_ids = fields.Many2many('icd.codes', string="ICD10")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
