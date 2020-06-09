from . import models
from . import wizard
from odoo import models, api
from xlrd import open_workbook
import os.path
from odoo import SUPERUSER_ID


def post_init_check(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    user_ids = env['res.users'].search([])
    group_id = env.ref('stock.group_stock_multi_locations')
    group_id.write({'users': [(6, 0, user_ids.ids)]})
    param_obj = env['ir.config_parameter']
    param_obj.sudo().set_param('stock.group_stock_multi_locations', env.ref('stock.group_stock_multi_locations'))
    group_stock_multi_locations = bool(param_obj.sudo().get_param('stock.group_stock_multi_locations'))
    config_obj = env['res.config.settings']
    config_id = config_obj.sudo().search([], limit=1, order='id desc')
    if config_id:
        config_id.sudo().write({
            'multi_sales_price': True
        })
    module_name = env['ir.module.module'].search([('name', '=', 'TOMS'), ('demo', '=', True)], limit=1)
    if module_name:
        stage_inprogress = env.ref("project.project_stage_1")
        stage_done = env.ref("project.project_stage_2")
        stage_to_do = env.ref("project.project_stage_0")
        if stage_done:
            stage_done.active = False
        if stage_inprogress:
            stage_inprogress.active = False
        if stage_to_do:
            stage_to_do.active = False

    env['res.lang'].search([('active', '=', True)]).write({
        'date_format': '%d/%m/%Y'
    })
    env['res.company'].search([]).write({
        'external_report_layout_id': env['ir.ui.view'].search([('key', '=', 'web.external_layout_background')],
                                                              limit=1).id,
    })
    try:
        env['res.company'].search([]).write({
            'account_sale_tax_id': env.ref('l10n_za.za_sale_vat_tax').id or False,
            'account_purchase_tax_id': env.ref('l10n_za.za_purchase_vat_tax').id or False,
        })
    except Exception:
        pass
    env['ir.config_parameter'].sudo().set_param('sale.sale_pricelist_setting', 'percentage')
    env['account.tax'].sudo().search([('name', '=', 'Tax 15.00%'), ('type_tax_use', 'in', ['sale', 'purchase'])]).write(
        {
            'active': False
        })

    return True
    #     paths = os.path.join(os.path.dirname(os.path.abspath(__file__)))
#     path = os.path.expanduser(paths + '/data/toms_demo_data.xlsx')
#     workbook = open_workbook(path, on_demand=True)
#     count = 0
#     sheet = workbook.sheet_by_index(0)
#     sheet2 = workbook.sheet_by_index(1)
#     sheet3 = workbook.sheet_by_index(2)
#     sheet4 = workbook.sheet_by_index(4)
#     sheet5 = workbook.sheet_by_index(5)
#     for row_no in range(sheet.nrows):
#         if row_no <= 0:
#             fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
#         else:
#             line = list((map(lambda row:isinstance(row.value, (list)) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no))))
#             if line and line[1] and line[2] and line[3] and line[4]:
#                 partner_id = env['res.partner'].search([('name','=',str(line[1]).strip()),
#                                                     ('ref','=',str(line[2]).strip()),
#                                                     ('is_a_medical_aid_administrator','=',False)])
#                 if not partner_id:
#                     partner_id = env['res.partner'].create({'name':str(line[1]).strip(),
#                                                           'ref':str(line[2]).strip(),
#                                                           'company_type':str(line[4]).strip().lower(),
#                                                           'is_a_medical_aid_administrator':line[3],
#                                                           'admin_code':line[0].split('.')[0],
#                                                           'customer':False
#                                                            })
#                 else:
#                     partner_id = partner_id.filtered(lambda l:l.company_type == str(line[4]).strip().lower())
#                     partner_id.write({'is_a_medical_aid_administrator':line[3],
#                                         'admin_code':line[0].split('.')[0],
#                                         'customer':False})                                                                     
# 
#     for row_no in range(sheet2.nrows):
#         if row_no <= 0:
#             fields = list(map(lambda row:row.value.encode('utf-8'), sheet2.row(row_no)))
#         else:
#             line = list((map(lambda row:isinstance(row.value, (list)) and row.value.encode('utf-8') or str(row.value), sheet2.row(row_no))))
#             
#             if line and line[0] and line[1] and line[2] and line[3] and line[4] and line[5] and line[6]:
#                 rec_id = env['res.partner'].search([('admin_code','=',line[2].split('.')[0])])
#                 if rec_id:
#                     serach_partner_id = env['res.partner'].search([('name','=',line[1].strip())],limit=1)
#                     if not serach_partner_id: 
#                         partner_id = env['res.partner'].create({
#                             'name':str(line[1]).strip(),
#                             'administrator_id':rec_id.id,
#                             'is_contracted': True if line[3] == "Yes" else False,
#                             'period_cycle':str(line[4]).strip(),
#                             'is_a_medical_aid':True,
#                             'medical_aid_key':line[0].split('.')[0],
#                             'company_type':str(line[6]).strip().lower(),
#                             'customer':False
#                             })
#                     else:
#                         serach_partner_id = serach_partner_id.filtered(lambda l:l.company_type == str(line[6]).strip().lower())
#                         serach_partner_id.write({'is_a_medical_aid':True,
#                                       'is_contracted': True if line[3] == "Yes" else False,
#                                       'customer':False,
#                                       'medical_aid_key':line[0].split('.')[0],
#                                       'administrator_id':rec_id.id,
#                                       'period_cycle':str(line[4]).strip(),
#                                       'company_type':str(line[6]).strip().lower(),
#                                     })
#                 else:
#                     serach_partner_id = env['res.partner'].search([('name','=',line[1].strip())],limit=1)
#                     if not serach_partner_id:
#                         partner_id = env['res.partner'].create({
#                                     'name':str(line[1]).strip(),
#                                     'is_contracted': True if line[3] == "Yes" else False,
#                                     'period_cycle':str(line[4]).strip(),
#                                     'is_a_medical_aid':True,
#                                     'medical_aid_key':line[0].split('.')[0],
#                                     'company_type':str(line[6]).strip().lower(),
#                                     'customer':False
#                                     })
#                     else:
#                         serach_partner_id = serach_partner_id.filtered(lambda l:l.company_type == str(line[6]).strip().lower())
#                         serach_partner_id.write({'is_a_medical_aid':True,
#                                       'is_contracted': True if line[3] == "Yes" else False,
#                                       'customer':False,
#                                       'medical_aid_key':line[0].split('.')[0],
#                                       'period_cycle':str(line[4]).strip(),
#                                       'company_type':str(line[6]).strip().lower(),
#                                     })
# 
#     for row_no in range(sheet3.nrows):
#         if row_no <= 0:
#             fields = list(map(lambda row:row.value.encode('utf-8'), sheet3.row(row_no)))
#         else:
#             line = list((map(lambda row:isinstance(row.value, (list)) and row.value.encode('utf-8') or str(row.value), sheet3.row(row_no))))
#             if line and line[0] and line[1] and line[2] and line[3]:
#                 rec_id = env['res.partner'].search([('medical_aid_key','=',line[0].split('.')[0])])
#                 
#                 if rec_id:
#                     medical_code = ''    
#                     if line[2].split('.')[0] == '0':
#                         medical_code = 'saoa'  
#                     elif line[2].split('.')[0] == '1':
#                         medical_code = 'ppn1'
#                     elif line[2].split('.')[0] == '2':
#                         medical_code = 'ppn2'
#                     elif line[2].split('.')[0] == '3':
#                         medical_code = 'ppn3'
#                     elif line[2].split('.')[0] == '4':
#                         medical_code = 'nedcor'
#                     medical_aid_plan_id = env['medical.aid.plan'].create({
#                                                                         'code': medical_code,
#                                                                         'name':str(line[1]).strip(),
#                                                                         'medical_aid_id':rec_id.id,
#                                                                         })
# 
#     for row_no in range(sheet4.nrows):
#         if row_no <= 0:
#             fields = list(map(lambda row:row.value.encode('utf-8'), sheet4.row(row_no)))
#         else:
#             line = list((map(lambda row:isinstance(row.value, (list)) and row.value.encode('utf-8') or str(row.value), sheet4.row(row_no))))
#             if line and line[0] and line[1]:
#                 env['icd.codes'].create({
#                                          'code':str(line[0]).strip(),
#                                          'name':str(line[1]).strip()
#                                         })
# 
#     for row_no in range(sheet5.nrows):
#         if row_no <= 0:
#             fields = list(map(lambda row:row.value.encode('utf-8'), sheet5.row(row_no)))
#         else:
#             line = list((map(lambda row:isinstance(row.value, (list)) and row.value.encode('utf-8') or str(row.value), sheet5.row(row_no))))
#             if line and line[0] and line[1]:
#                 env['nappi.codes'].create({
#                                          'code':line[0].split('.')[0],
#                                          'name':str(line[1]).strip()
#                                         })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
