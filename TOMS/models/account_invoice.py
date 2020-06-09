from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError, UserError, AccessError
from odoo.tools import safe_eval

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    patient_id = fields.Many2one('res.partner', string="Patient")
    optometrist_id = fields.Many2one('res.users', string="Optometrist")
    dispenser_id = fields.Many2one('res.users', string="Dispenser")
    frontliner_id = fields.Many2one('res.users', string="Frontliner")
    exam_date = fields.Date(string="Exam Date")
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    refund_reason_id = fields.Many2one('account.invoice.refund.reason', string="Refund Reason")
    approved_amount = fields.Monetary(string='Total Approved Amount',
                                      store=True, readonly=True,compute='_compute_approved_amount')

    @api.depends('invoice_line_ids.approved_amount')
    def _compute_approved_amount(self):
        for line_id in self:
            line_id.approved_amount = sum(line.approved_amount for line in line_id.invoice_line_ids)

    @api.multi
    @api.returns('self')
    def refund(self, date_invoice=None, date=None, description=None, journal_id=None, refund_reason_id=None):
        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self._prepare_refund(invoice, date_invoice=date_invoice, date=date,
                                          description=description, journal_id=journal_id)
            if refund_reason_id:
                values['refund_reason_id'] = refund_reason_id
            refund_invoice = self.create(values)
            if invoice.type == 'out_invoice':
                message = _(
                    "This customer invoice credit note has been created from: <a href=# data-oe-model=account.invoice data-oe-id=%d>%s</a><br>Reason: %s") % (
                              invoice.id, invoice.number, description)
            else:
                message = _(
                    "This vendor bill credit note has been created from: <a href=# data-oe-model=account.invoice data-oe-id=%d>%s</a><br>Reason: %s") % (
                              invoice.id, invoice.number, description)

            refund_invoice.message_post(body=message)
            new_invoices += refund_invoice
        return new_invoices

    @api.multi
    def action_invoice_open(self):
        if self.type in ['out_invoice', 'out_refund']:
            for each in self.invoice_line_ids.filtered(lambda l: not l.icd_codes_ids):
                raise ValidationError(
                    _('[%s] %s , does not have an ICD Code. Please assign an ICD code to continue.') % (
                        each.product_id.default_code, each.product_id.name))
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(lambda inv: inv.amount_total < 0):
            raise UserError(_(
                "You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()

    @api.multi
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(account_invoice, self)._onchange_partner_id()
        self.pricelist_id = False
        if self.partner_id:
            self.pricelist_id = self.partner_id.property_product_pricelist.id
        return res

    @api.model
    def _refund_cleanup_lines(self, lines):
        result = []
        for line in lines:
            values = {}
            for name, field in line._fields.items():
                if name in MAGIC_COLUMNS:
                    continue
                elif field.type == 'many2one':
                    values[name] = line[name].id
                elif field.type not in ['many2many', 'one2many']:
                    values[name] = line[name]
                elif name == 'invoice_line_tax_ids':
                    values[name] = [(6, 0, line[name].ids)]
                elif name == 'analytic_tag_ids':
                    values[name] = [(6, 0, line[name].ids)]
                elif name == 'icd_codes_ids':
                    values[name] = [(6, 0, line[name].ids)]
            result.append((0, 0, values))
        return result

    def _get_refund_common_fields(self):
        return ['partner_id', 'patient_id','payment_term_id', 'account_id', 'currency_id', 'journal_id']

class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    final_rx_id = fields.Many2one('clinical.final.rx', string="Clinical Final RX")
    contact_final_rx_id = fields.Many2one('clinical.final.rx.contact', string="Contact Clinical Final RX")
    saoa_code_id = fields.Many2one('saoa.codes', related='product_id.saoa_code_id', string="SAOA Code")
    ppn1_code_id = fields.Many2one('ppn1.codes', related='product_id.ppn1_code_id', string="PPN1 Code")
    icd_codes_ids = fields.Many2many('icd.codes', string="ICD10")
    approved_amount = fields.Float(string="Scheme Balance")
    balance_amount = fields.Float("Patient Balance")
    claim_status = fields.Char(string="Status")

    @api.multi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(account_invoice_line, self)._onchange_product_id()
        if self.product_id:
            vals = {}
            domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
            if not self.uom_id or (self.product_id.uom_id.id != self.uom_id.id):
                vals['product_uom'] = self.product_id.uom_id
                vals['product_uom_qty'] = 1.0

            product = self.product_id.with_context(
                lang=self.invoice_id.partner_id.lang,
                partner=self.invoice_id.partner_id.id,
                quantity=vals.get('product_uom_qty') or self.quantity,
                date=self.invoice_id.date_invoice,
                pricelist=self.invoice_id.pricelist_id.id,
                uom=self.product_id.uom_id.id
            )
            self._compute_tax_id()
            if self.invoice_id.pricelist_id and self.invoice_id.partner_id:
                vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                    self._get_display_price(product), product.taxes_id, self.invoice_line_tax_ids, self.company_id)
                self.update(vals)
        return res

    @api.onchange('uom_id', 'quantity')
    def product_uom_id_change(self):
        if not self.uom_id or not self.product_id:
            self.price_unit = 0.0
            return
        if self.invoice_id.pricelist_id and self.invoice_id.partner_id:
            product = self.product_id.with_context(
                lang=self.invoice_id.partner_id.lang,
                partner=self.invoice_id.partner_id.id,
                quantity=self.quantity,
                date=self.invoice_id.date_invoice,
                pricelist=self.invoice_id.pricelist_id.id,
                uom=self.product_id.uom_id.id,
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                      product.taxes_id,
                                                                                      self.invoice_line_tax_ids,
                                                                                      self.company_id)

    @api.multi
    def _get_display_price(self, product):
        if self.invoice_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.invoice_id.pricelist_id.id).price
        final_price, rule_id = self.invoice_id.pricelist_id.get_product_price_rule(self.product_id,
                                                                                   self.product_uom_qty or 1.0,
                                                                                   self.invoice_id.partner_id)
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
            line.invoice_line_tax_ids = taxes


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def load_for_current_company(self, sale_tax_rate, purchase_tax_rate):
        """ Installs this chart of accounts on the current company, replacing
        the existing one if it had already one defined. If some accounting entries
        had already been made, this function fails instead, triggering a UserError.

        Also, note that this function can only be run by someone with administration
        rights.
        """
        self.ensure_one()
        company = self.env.user.company_id
        # Ensure everything is translated to the company's language, not the user's one.
        self = self.with_context(lang=company.partner_id.lang)
        if not self.env.user._is_admin():
            raise AccessError(_("Only administrators can load a charf of accounts"))

        existing_accounts = self.env['account.account'].search([('company_id', '=', company.id)])
        if existing_accounts:
            # we tolerate switching from accounting package (localization module) as long as there isn't yet any accounting
            # entries created for the company.
            if self.existing_accounting(company):
                raise UserError(
                    _('Could not install new chart of account as there are already accounting entries existing.'))

            # delete accounting properties
            prop_values = ['account.account,%s' % (account_id,) for account_id in existing_accounts.ids]
            existing_journals = self.env['account.journal'].search([('company_id', '=', company.id)])
            if existing_journals:
                prop_values.extend(['account.journal,%s' % (journal_id,) for journal_id in existing_journals.ids])
            accounting_props = self.env['ir.property'].search([('value_reference', 'in', prop_values)])
            if accounting_props:
                accounting_props.unlink()

            # delete account, journal, tax, fiscal position and reconciliation model
            models_to_delete = ['account.reconcile.model', 'account.fiscal.position', 'account.tax', 'account.move',
                                'account.journal']
            for model in models_to_delete:
                res = self.env[model].search([('company_id', '=', company.id)])
                if len(res):
                    res.unlink()
            existing_accounts.unlink()

        company.write({'currency_id': self.currency_id.id,
                       'anglo_saxon_accounting': self.use_anglo_saxon,
                       'bank_account_code_prefix': self.bank_account_code_prefix,
                       'cash_account_code_prefix': self.cash_account_code_prefix,
                       'transfer_account_code_prefix': self.transfer_account_code_prefix,
                       'chart_template_id': self.id
                       })

        # set the coa currency to active
        self.currency_id.write({'active': True})

        # When we install the CoA of first company, set the currency to price types and pricelists
        if company.id == 1:
            for reference in ['product.list_price', 'product.standard_price', 'product.list0']:
                try:
                    tmp2 = self.env.ref(reference).write({'currency_id': self.currency_id.id})
                except ValueError:
                    pass

        # If the floats for sale/purchase rates have been filled, create templates from them
        self._create_tax_templates_from_rates(company.id, sale_tax_rate, purchase_tax_rate)

        # Install all the templates objects and generate the real objects
        acc_template_ref, taxes_ref = self._install_template(company, code_digits=self.code_digits)

        # Set the transfer account on the company
        company.transfer_account_id = \
            self.env['account.account'].search([('code', '=like', self.transfer_account_code_prefix + '%')])[0]

        # Create Bank journals
        self._create_bank_journals(company, acc_template_ref)

        # Create the current year earning account if it wasn't present in the CoA
        company.get_unaffected_earnings_account()

        # set the default taxes on the company

        sale_tax_id = self.env['account.tax'].search(
            [('name', '=', 'VAT on Sales (15%)'), ('type_tax_use', 'in', ('sale', 'all')),
             ('company_id', '=', company.id)], limit=1).id
        company.account_sale_tax_id = sale_tax_id
        if not sale_tax_id:
            company.account_sale_tax_id = self.env['account.tax'].search(
                [('type_tax_use', 'in', ('sale', 'all')), ('company_id', '=', company.id)], limit=1).id

        purchase_tax_id = self.env['account.tax'].search(
            [('name', '=', 'VAT on Purchases (15%)'), ('type_tax_use', 'in', ('purchase', 'all')),
             ('company_id', '=', company.id)], limit=1).id
        company.account_purchase_tax_id = purchase_tax_id
        if not purchase_tax_id:
            company.account_purchase_tax_id = self.env['account.tax'].search(
                [('type_tax_use', 'in', ('purchase', 'all')), ('company_id', '=', company.id)], limit=1).id
        return {}


class AccountInvoiceRefund(models.TransientModel):
    """Credit Notes"""

    _inherit = "account.invoice.refund"

    refund_reason_id = fields.Many2one('account.invoice.refund.reason', string="Refund Reason")

    @api.multi
    def compute_refund(self, mode='refund'):
        inv_obj = self.env['account.invoice']
        inv_tax_obj = self.env['account.invoice.tax']
        inv_line_obj = self.env['account.invoice.line']
        context = dict(self._context or {})
        xml_id = False

        for form in self:
            created_inv = []
            date = False
            description = False
            for inv in inv_obj.browse(context.get('active_ids')):
                if inv.state in ['draft', 'cancel']:
                    raise UserError(_('Cannot create credit note for the draft/cancelled invoice.'))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise UserError(_(
                        'Cannot create a credit note for the invoice which is already reconciled, invoice should be unreconciled first, then only you can add credit note for this invoice.'))

                date = form.date or False
                description = form.description or inv.name
                refund = inv.refund(form.date_invoice, date, description, inv.journal_id.id, form.refund_reason_id.id)

                created_inv.append(refund.id)
                if mode in ('cancel', 'modify'):
                    movelines = inv.move_id.line_ids
                    to_reconcile_ids = {}
                    to_reconcile_lines = self.env['account.move.line']
                    for line in movelines:
                        if line.account_id.id == inv.account_id.id:
                            to_reconcile_lines += line
                            to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                        if line.reconciled:
                            line.remove_move_reconcile()
                    refund.action_invoice_open()
                    for tmpline in refund.move_id.line_ids:
                        if tmpline.account_id.id == inv.account_id.id:
                            to_reconcile_lines += tmpline
                    to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
                    if mode == 'modify':
                        invoice = inv.read(inv_obj._get_refund_modify_read_fields())
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(invoice['invoice_line_ids'])
                        invoice_lines = inv_obj.with_context(mode='modify')._refund_cleanup_lines(invoice_lines)
                        tax_lines = inv_tax_obj.browse(invoice['tax_line_ids'])
                        tax_lines = inv_obj._refund_cleanup_lines(tax_lines)
                        invoice.update({
                            'type': inv.type,
                            'date_invoice': form.date_invoice,
                            'state': 'draft',
                            'number': False,
                            'invoice_line_ids': invoice_lines,
                            'tax_line_ids': tax_lines,
                            'date': date,
                            'origin': inv.origin,
                            'fiscal_position_id': inv.fiscal_position_id.id,
                        })
                        for field in inv_obj._get_refund_common_fields():
                            if inv_obj._fields[field].type == 'many2one':
                                invoice[field] = invoice[field] and invoice[field][0]
                            else:
                                invoice[field] = invoice[field] or False
                        inv_refund = inv_obj.create(invoice)
                        body = _(
                            'Correction of <a href=# data-oe-model=account.invoice data-oe-id=%d>%s</a><br>Reason: %s') % (
                                   inv.id, inv.number, description)
                        inv_refund.message_post(body=body)
                        if inv_refund.payment_term_id.id:
                            inv_refund._onchange_payment_term_date_invoice()
                        created_inv.append(inv_refund.id)
                xml_id = inv.type == 'out_invoice' and 'action_invoice_out_refund' or \
                         inv.type == 'out_refund' and 'action_invoice_tree1' or \
                         inv.type == 'in_invoice' and 'action_invoice_in_refund' or \
                         inv.type == 'in_refund' and 'action_invoice_tree2'
        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            if mode == 'modify':
                # When refund method is `modify` then it will directly open the new draft bill/invoice in form view
                if inv_refund.type == 'in_invoice':
                    view_ref = self.env.ref('account.invoice_supplier_form')
                else:
                    view_ref = self.env.ref('account.invoice_form')
                result['views'] = [(view_ref.id, 'form')]
                result['res_id'] = inv_refund.id
            else:
                invoice_domain = safe_eval(result['domain'])
                invoice_domain.append(('id', 'in', created_inv))
                result['domain'] = invoice_domain
            return result
        return True


class AccountInvoiceRefundReason(models.Model):
    _name = 'account.invoice.refund.reason'
    _description = 'Account Invoice Refund Reason'

    name = fields.Char(string="Name")
