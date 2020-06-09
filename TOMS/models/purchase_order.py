from odoo import models, fields, api, _


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    clinical_exam_id = fields.Many2one('clinical.examination', string="Exam")
    final_rx_id = fields.Many2one('clinical.final.rx', string="Final Rx")
    contact_final_rx_id = fields.Many2one('clinical.final.rx.contact', string="Contact Final Rx")
    project_task_id = fields.Many2one('project.task', string="Job")
    job_number = fields.Char(related="project_task_id.job_number")
