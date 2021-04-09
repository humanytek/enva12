# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

NAME_MONTH=[
('01','ENERO'),
('02','FEBRERO'),
('03','MARZO'),
('04','ABRIL'),
('05','MAYO'),
('06','JUNIO'),
('07','JULIO'),
('08','AGOSTO'),
('09','SEPTIEMBRE'),
('10','OCTUBRE'),
('11','NOVIEMBRE'),
('12','DICIEMBRE'),

]

class BussinesDays(models.Model):
    _name = 'bussines.days'


    name = fields.Selection(
        NAME_MONTH,
        'Mes',
        required=True,
        store=True,
    )

    bussines_days = fields.Integer(
        string= 'Dias Habiles',
        required=True,
        store = True,
    )

    year = fields.Char(
        string = 'Año',
        required= True,
        store = True,
    )
