from odoo import models,fields,api,_


class icd_codes_model(models.Model):
    _name = 'icd.codes'
    _order='icd_codes_category_id asc'
    _description = 'Icd Codes'

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    comment = fields.Text(string="Comment")
    icd_codes_category_id = fields.Many2one('icd.codes.category', string="Category")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        record_ids = []
        if name:
            record_ids = self._search([('code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        if not record_ids:
            record_ids = self._search([('code', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(record_ids).name_get()

    @api.multi
    def name_get(self):
        result = []
#         for each in self:
#             if each.icd_codes_category_id:
#                 name = each.code + ' - ' + each.icd_codes_category_id.name
#                 result.append((each.id,name))
#             else:
#                 result.append((each.id,each.code if each.code else each.name))
#         return result
        for each in self:
            result.append((each.id,each.code if each.code else each.name))
        return result


class nappi_codes_model(models.Model):
    _name = 'nappi.codes'
    _description = "Nappi Codes"

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    comment = fields.Text(string="Comment")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        record_ids = []
        if name:
            record_ids = self._search([('code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        if not record_ids:
            record_ids = self._search([('code', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(record_ids).name_get()


    @api.multi
    def name_get(self):
        result = []
        for each in self:
            result.append((each.id,each.code if each.code else each.name))
        return result


class saoa_codes_model(models.Model):
    _name = 'saoa.codes'
    _description = 'SAOA Codes'

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    comment = fields.Text(string="Comment")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        record_ids = []
        if name:
            record_ids = self._search([('code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        if not record_ids:
            record_ids = self._search([('code', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(record_ids).name_get()

    @api.multi
    def name_get(self):
        result = []
        for each in self:
            result.append((each.id,each.code if each.code else each.name))
        return result


class old_code_model(models.Model):
    _name = 'old.codes'
    _description = 'Old Codes'

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    comment = fields.Text(string="Comment")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        record_ids = []
        if name:
            record_ids = self._search([('code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        if not record_ids:
            record_ids = self._search([('code', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(record_ids).name_get()

    @api.multi
    def name_get(self):
        result = []
        for each in self:
            result.append((each.id,each.code if each.code else each.name))
        return result

class ppn1_codes_model(models.Model):
    _name = 'ppn1.codes'
    _description = 'ppn1 codes'

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    comment = fields.Text(string="Comment")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        record_ids = []
        if name:
            record_ids = self._search([('code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        if not record_ids:
            record_ids = self._search([('code', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(record_ids).name_get()

    @api.multi
    def name_get(self):
        result = []
        for each in self:
            result.append((each.id,each.code if each.code else each.name))
        return result

class icd_codes_category(models.Model):
    _name = 'icd.codes.category'
    _description = 'Icd Codes Category'

    name = fields.Char(String="Category Name")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: