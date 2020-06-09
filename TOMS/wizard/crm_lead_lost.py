from odoo import models,fields,api,_


class crm_lead_lost(models.TransientModel):
	_inherit = 'crm.lead.lost'

	@api.multi
	def action_cancel_examination(self):
		if self.lost_reason_id:
			rec_id = self.env['calendar.event'].browse(self.env.context['active_id'])
			rec_id.state = 'cancel'
			rec_id.lost_reason_id = self.lost_reason_id
