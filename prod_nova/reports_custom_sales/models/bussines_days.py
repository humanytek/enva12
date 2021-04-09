# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

NAME_MONTH=[
('1','ENERO'),
('2','FEBRERO'),
('3','MARZO'),
('4','ABRIL'),
('5','MAYO'),
('6','JUNIO'),
('7','JULIO'),
('8','AGOSTO'),
('9','SEPTIEMBRE'),
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
