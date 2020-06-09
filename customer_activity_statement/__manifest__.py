# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Partner Activity Statement',
    'version': '11.0.2.0.14',
    'category': 'Accounting & Finance',
    'summary': 'OCA Financial Reports',
    'author': "Eficent, Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/account-financial-reporting',
    'license': 'AGPL-3',
    'depends': [
        'account_accountant','account','web'
    ],
    'data': [
        'views/statement.xml',
        'data/mail_template_data.xml',
        'data/partner_activity_statement_cron.xml',
        'wizard/customer_activity_statement_wizard.xml',
        'views/res_config_view.xml',
    ],
    'installable': True,
    'application': False,
}
