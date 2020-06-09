from odoo import models,fields,api,_


class Product_Category(models.Model):
    _inherit = "product.category"

    @api.multi
    @api.onchange('parent_id')
    def onchange_parent_category(self):
        self.update({
            'property_account_creditor_price_difference_categ' : self.parent_id.property_account_creditor_price_difference_categ.id,
            'property_account_income_categ_id':self.parent_id.property_account_income_categ_id.id,
            'property_account_expense_categ_id':self.parent_id.property_account_expense_categ_id.id,
            'property_stock_account_input_categ_id':self.parent_id.property_stock_account_input_categ_id.id,
            'property_stock_account_output_categ_id':self.parent_id.property_stock_account_output_categ_id,
            'property_stock_valuation_account_id':self.parent_id.property_stock_valuation_account_id.id,
            'property_stock_journal':self.parent_id.property_stock_journal.id
        })