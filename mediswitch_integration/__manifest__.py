# -*- coding: utf-8 -*-
#################################################################################
# Author      : Humint Business Information Systems (<www.humint.co.za>)
# Copyright(c): 2019 Humint Business Information Systems
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
    'name': 'Mediswitch Integration',
    'summary': 'Mediswitch Integration',
    'version': '1.56',
    'description': """Mediswitch Integration""",
    'author': 'Humint Business Information Systems',
    'category': 'account',
    'website': "http://www.humint.co.za",
    'depends': ['base', 'account', 'TOMS','account_cancel'],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/account_invoice.xml',
        'views/res_users.xml',
        'views/medical_aid_claims.xml',
        'wizard/response_wizard.xml'
    ],
    'qweb': [
        'static/src/xml/global_fetch.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
