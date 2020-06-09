from odoo.tests import common, Form
from odoo.addons.test_mail.tests.common import mail_new_test_user


class TestTOMSCommon(common.TransactionCase):

    def test_add_dependant(self):
        self.res_users = mail_new_test_user(self.env, login='normal_user',
                                            groups='base.group_user',
                                            name='Group User', email='group@example.com')

        self.res_partner_ind = Form(self.res_users.partner_id)
        self.res_partner_ind.company_type = 'person'
        self.res_partner_ind.street = 'Test'
        self.res_partner_ind.street2 = 'Test'
        self.res_partner_ind.city = 'Test'
        self.res_partner_ind.state_id = self.env(user=self.res_users).ref('base.state_in_gj')
        self.res_partner_ind.zip = '123456'
        self.res_partner_ind.country_id = self.env(user=self.res_users).ref('base.in')
        self.res_partner_ind.phone = '6548423184'
        self.res_partner_ind.mobile = '6548423184'
        self.res_partner_ind.email = "res_ind@test.com"
        self.res_partner_ind.title = self.env(user=self.res_users).ref('base.res_partner_title_mister')
        self.res_partner_ind.co_reg_no = "1234/982375/12"
        self.res_partner_ind.vat = "6548423184"
        self.res_partner_ind.save()

        self.res_partner_com = Form(self.res_users.partner_id)
        self.res_partner_com.company_type = 'company'
        self.res_partner_com.trading_as = 'company'
        self.res_partner_com.street = 'Test'
        self.res_partner_com.street2 = 'Test'
        self.res_partner_com.city = 'Test'
        self.res_partner_com.state_id = self.env(user=self.res_users).ref('base.state_in_gj')
        self.res_partner_com.zip = '123456'
        self.res_partner_com.country_id = self.env(user=self.res_users).ref('base.in')
        self.res_partner_com.phone = '7845123298'
        self.res_partner_com.mobile = '7845123298'
        self.res_partner_com.email = 'res_com@test.com'
        self.res_partner_com.co_reg_no = "1234/546784/13"
        self.res_partner_com.vat = "7845123298"
        self.res_partner_com.save()

        self.res_partner_com_child_1 = self.env['res.partner'].create({
            'name': 'Test Child1',
            'title': self.env(user=self.res_users).ref('base.res_partner_title_mister').id,
            'function': self.function.id,
            'mobile': '789456123456',
            'parent_id': self.res_partner_com.id,
            'email': 'child_1@test.com',
            'is_dependent': True
        })
        self.assertEqual(self.res_partner_com_child_1.parent_id.id, self.res_partner_com.id,
                         "Contact is created successfully")
