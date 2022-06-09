# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models,_
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    mantto_requisition_id = fields.Many2one(
    'maintenance.requisition',
    string='Requisicion de Mantto',
    copy=False
    )

    requisitionpurchase_count=fields.Integer(
    compute='_count_rp',
    string='Requisition Purchase count',

    )

    area_id = fields.Many2one(
    comodel_name = 'maintenance.area',
    string = 'Area',
    store = True,
    )


    def name_get(self):
        result = []
        for s in self:
            name = s.code+ ' ' + s.name
            result.append((s.id, name))
        return result


    def _count_rp(self):
        results = self.env['purchase.requisition'].read_group([('maintenance_request_id', 'in', self.ids)], ['maintenance_request_id'], ['maintenance_request_id'])
        dic = {}
        for x in results: dic[x['maintenance_request_id'][0]] = x['maintenance_request_id_count']
        for record in self: record['requisitionpurchase_count'] = dic.get(record.id, 0)


    @api.onchange('mantto_requisition_id')
    def _onchange_mantto_requisition_id(self):
        if not self.mantto_requisition_id:
            return

        mantto_requisition = self.mantto_requisition_id

        self.name=mantto_requisition.reference
        self.priority=mantto_requisition.priority
        self.note=mantto_requisition.note
        self.request_date=mantto_requisition.date_request
        self.user_id=mantto_requisition.assigned_id
        # _logger.info('USUARIO %s', mantto_requisition.assigned_id.id)
        self.area_id=mantto_requisition.area_id


    @api.onchange('equipment_id')
    def onchange_equipment_id(self):
        if self.mantto_requisition_id:
            mantto_requisition = self.mantto_requisition_id
            self.user_id=mantto_requisition.assigned_id
        else:
            if self.equipment_id:
                self.user_id = self.equipment_id.technician_user_id if self.equipment_id.technician_user_id else self.equipment_id.category_id.technician_user_id
                self.category_id = self.equipment_id.category_id
                if self.equipment_id.maintenance_team_id:
                    self.maintenance_team_id = self.equipment_id.maintenance_team_id.id

    @api.onchange('category_id')
    def onchange_category_id(self):
        if self.mantto_requisition_id:
            mantto_requisition = self.mantto_requisition_id
            self.user_id=mantto_requisition.assigned_id
        else:
            if not self.user_id or not self.equipment_id or (self.user_id and not self.equipment_id.technician_user_id):
                self.user_id = self.category_id.technician_user_id
