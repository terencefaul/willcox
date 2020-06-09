from odoo.addons import decimal_precision as dp
from datetime import datetime

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import math

class clinical_final_rx_contact(models.Model):
    _name = 'clinical.final.rx.contact'
    _description = 'Clinical Final RX Contact'

    @api.model
    def create(self, vals):
        res = super(clinical_final_rx_contact, self).create(vals)
        if res.final_rx_id and res.dispense:
            rec = res.read()[0]
            rec.update({'final_rx_id': False, 'final_rx_dis_id': res.final_rx_id.id, 'old_id': res.id})
            self.create(rec)
        return res

    @api.multi
    def write(self, vals):
        res = super(clinical_final_rx_contact, self).write(vals)
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

#    name = fields.Selection([('Trial Contact Lens', 'Trial Contact Lens'),
#                             ('Final Contact Lens', 'Final Contact Lens')], string="Name")
    name = fields.Char(string='Name', required=True)
    od_syh = fields.Float(string="Sph")
    od_cyl = fields.Float(string="Cyl")
    od_axis = fields.Integer(string="Axis")
    od_add = fields.Float(string="Add")
    od_va = fields.Float(string="VA")
    os_syh = fields.Float(string="Sph ")
    os_cyl = fields.Float(string="Cyl ")
    os_axis = fields.Integer(string="Axis ")
    os_add = fields.Float(string="Add ")
    os_va = fields.Float(string="VA ")
    dispense = fields.Boolean(string="Dispense", default=True)
    final_rx_id = fields.Many2one('clinical.examination')
    final_rx_dis_id = fields.Many2one('clinical.examination')
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
    clinical_final_rx_ids = fields.One2many('dispensing.examination.line', 'contact_clinical_final_rx_id')
    task_id = fields.Many2one('project.task', copy=False)
    invoice_id = fields.Many2one(related="final_rx_dis_id.invoice_id")
    old_id = fields.Many2one('clinical.final.rx')

    @api.onchange('name')
    def onchange_name(self):
        if self.name and self.name == 'Final Contact Lens':
            self.dispense = True
        else:
            self.dispense = False

    @api.multi
    def get_subjective_lines(self, each):
        subjective_line = {
            'od_syh': each.get('od_syh') if isinstance(each, dict) else each['od_syh'],
            'od_cyl': each.get('od_cyl') if isinstance(each, dict) else each['od_cyl'],
            'od_axis': each.get('od_axis') if isinstance(each, dict) else each['od_axis'],
            'od_add': each.get('od_add') if isinstance(each, dict) else each['od_add'],
            'od_va': each.get('od_va') if isinstance(each, dict) else each['od_va'],
            'os_syh': each.get('os_syh') if isinstance(each, dict) else each['os_syh'],
            'os_cyl': each.get('os_cyl') if isinstance(each, dict) else each['os_cyl'],
            'os_axis': each.get('os_axis') if isinstance(each, dict) else each['os_axis'],
            'os_add': each.get('os_add') if isinstance(each, dict) else each['os_add'],
            'os_va': each.get('os_va') if isinstance(each, dict) else each['os_va'],
        }
        return subjective_line

    @api.onchange('od_cyl', 'os_cyl')
    def onchange_cyl(self):
        if self.od_cyl and self.od_cyl > 0:
            self.od_cyl = self.od_cyl * -1
        if self.os_cyl and self.os_cyl > 0:
            self.od_cyl = self.od_cyl * -1



    @api.model
    def default_get(self, fieldlist):
        res = super(clinical_final_rx_contact, self).default_get(fieldlist)
        if self._context.get('contact_clinical_test_ids'):
            for each in self._context.get('contact_clinical_test_ids')[-1:]:
                for each_line in each[-1:]:
                    if each_line:
                        res.update(self.get_subjective_lines(each_line))
                    else:
                        clinical_examination_id = self.env['clinical.examination'].browse(
                            self._context.get('record_id'))
                        for each in clinical_examination_id.contact_clinical_test_ids.filtered(
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
            'res_model': 'wizard.final.rx.contact',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_clinical_final_rx_id': self.id,
                        'default_clinical_exam_id': self.final_rx_dis_id.id,
                        'default_diameter_r': self.final_rx_dis_id.diameter_r,
                        'default_diameter_l': self.final_rx_dis_id.diameter_l,
                        'default_base_curve_r': self.final_rx_dis_id.base_curve_r,
                        'default_base_curve_l': self.final_rx_dis_id.base_curve_l,
                        'default_over_fraction_r': self.final_rx_dis_id.over_fraction_r,
                        'default_over_fraction_l': self.final_rx_dis_id.over_fraction_l,
                        'default_axis_orientation_r': self.final_rx_dis_id.axis_orientation_r,
                        'default_axis_orientation_l': self.final_rx_dis_id.axis_orientation_l,
                        'default_movement_r': self.final_rx_dis_id.movement_r,
                        'default_movement_l': self.final_rx_dis_id.movement_l,
                        'default_sag_r': self.final_rx_dis_id.sag_r,
                        'default_sag_l': self.final_rx_dis_id.sag_l,
                        'default_landing_zone_r': self.final_rx_dis_id.landing_zone_r,
                        'default_landing_zone_l': self.final_rx_dis_id.landing_zone_l,
                        'default_notes_r': self.final_rx_dis_id.notes_r,
                        'default_notes_l': self.final_rx_dis_id.notes_l,
                        'default_wizard_final_rx_ids': product_fitting_detail,
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
                'contact_clinical_final_rx_id': self.id,
                'exam_id': self.final_rx_dis_id.id,
                'is_contact_lense_job': True
            })
            if res:
                self.task_id = res.id
            self.env['purchase.order'].create({
                'date_order': datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                'partner_ref': self.final_rx_dis_id.name + ":" + self.name,
                'clinical_exam_id': self.final_rx_dis_id.id,
                'contact_final_rx_id': self.id,
                'project_task_id': res.id,
                'partner_id': seller_id.id,
                'order_line': purchase_order_line,
            })
        else:
            raise ValidationError("Please select fitting products before you add to job.")


class dispensing_line_examination_contact(models.Model):
    _name = 'dispensing.examination.line.contact'
    _order = "clinical_final_rx_id"
    _description = 'Despensing Examination Line Contact'

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
    display_final_rx_id = fields.Many2one('clinical.final.rx', string="Final Rx")
    final_rx_flage = fields.Boolean()
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


class contact_clinical_test(models.Model):
    _name = 'contact.clinical.test'
    _description = 'Contact Clinical Test'

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


class contact_clinical_habitual(models.Model):
    _name = 'contact.clinical.habitual'
    _description = 'Contact Clinical Habitual'

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


class wizard_final_rx_contact(models.TransientModel):
    _name = 'wizard.final.rx.contact'
    _description = 'Wizard Final RX Contact'

    clinical_final_rx_id = fields.Many2one('clinical.final.rx.contact')
    clinical_exam_id = fields.Many2one('clinical.examination')
    invoice_id = fields.Many2one(related="clinical_exam_id.invoice_id")
#    name = fields.Selection([('Trial Contact Lens', 'Trial Contact Lens'),
#                             ('Final Contact Lens', 'Final Contact Lens')], string="Name",
#                            related="clinical_final_rx_id.name")
    name = fields.Char(string='Description', related="clinical_final_rx_id.name")
    od_syh = fields.Float(string="Sph", related="clinical_final_rx_id.od_syh")
    od_cyl = fields.Float(string="Cyl", related="clinical_final_rx_id.od_cyl")
    od_axis = fields.Integer(string="Axis", related="clinical_final_rx_id.od_axis")
    od_add = fields.Float(string="Add", related="clinical_final_rx_id.od_add")
    od_va = fields.Float(string="VA", related="clinical_final_rx_id.od_va")
    os_syh = fields.Float(string="Sph ", related="clinical_final_rx_id.os_syh")
    os_cyl = fields.Float(string="Cyl ", related="clinical_final_rx_id.os_cyl")
    os_axis = fields.Integer(string="Axis ", related="clinical_final_rx_id.os_axis")
    os_add = fields.Float(string="Add ", related="clinical_final_rx_id.os_add")
    os_va = fields.Float(string="VA ", related="clinical_final_rx_id.os_va")
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
    wizard_final_rx_ids = fields.One2many('wizard.final.rx.line.contact', 'final_rx_id')
    pricelist_id = fields.Many2one('product.pricelist', related="clinical_exam_id.dispensing_pricelist_id",
                                   string=" Pricelist")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency ", readonly=True,
                                  required=True)
    repurchase = fields.Boolean(related="clinical_final_rx_id.final_rx_dis_id.repurchase")
    l_r = fields.Selection(
        string='Eye',
        selection=[('l', 'Left'),
                   ('r', 'right'), ],
        required=True)
    dispensing_examination_line_id = fields.Many2one('dispensing.examination.line')

    @api.multi
    def submit_fitting_details(self):
        self.clinical_final_rx_id.write({
            'diameter_r': self.diameter_r,
            'diameter_l': self.diameter_l,
            'base_curve_r': self.base_curve_r,
            'base_curve_l': self.base_curve_l,
            'over_fraction_r': self.over_fraction_r,
            'over_fraction_l': self.over_fraction_l,
            'axis_orientation_r': self.axis_orientation_r,
            'axis_orientation_l': self.axis_orientation_l,
            'movement_r': self.movement_r,
            'movement_l': self.movement_l,
            'sag_r': self.sag_r,
            'sag_l': self.sag_l,
            'landing_zone_r': self.landing_zone_r,
            'landing_zone_l': self.landing_zone_l,
            'notes_r': self.notes_r,
            'notes_l': self.notes_l
        })
        final_rx_rec = self.wizard_final_rx_ids.filtered(lambda l: l.final_rx_flage != True)
        for each in final_rx_rec:
            self.clinical_exam_id.write({'dispensing_line_ids': [(0, 0, {
                'contact_clinical_final_rx_id': self.clinical_final_rx_id.id,
                'product_id': each.product_id.id,
                'name': each.name,
                'product_uom_qty': each.product_uom_qty,
                'price_unit': each.price_unit,
                'discount': each.discount,
                'tax_id': [(6, 0, each.tax_id.ids)],
                'icd_codes_ids': [(6, 0, each.icd_codes_ids.ids)],
                'final_rx_flage': True
            })]})


class wizard_final_rx_line_contact(models.TransientModel):
    _name = 'wizard.final.rx.line.contact'
    _description = 'Wizard Final RX Line Contact'

    final_rx_id = fields.Many2one('wizard.final.rx.contact', string="Final Rx")
    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('sale_ok', '=', True), ('categ_id.name', '=', 'Contact Lenses')],
                                 change_default=True, ondelete='restrict', required=True)
    name = fields.Text(string='Description', required=True)
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
    l_r  = fields.Selection(
        string='',
        selection=[('l', 'Left'),
                   ('r', 'Right'), ],
        required=False, )


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
        final_rx_id = self.env['clinical.final.rx.contact'].browse(self._context.get('default_clinical_final_rx_id'))
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
