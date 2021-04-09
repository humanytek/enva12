# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError

NAME_MONTH=[
('ENERO','01'),
('FEBRERO','02'),
('MARZO','03'),
('ABRIL','04'),
('MAYO','05'),
('JUNIO','06'),
('JULIO','07'),
('AGOSTO','08'),
('SEPTIEMBRE','09'),
('OCTUBRE','10'),
('NOVIEMBRE','11'),
('DICIEMBRE','12'),

]

class BussinesDays(models.Model):
    _name = 'bussines.day'

    name = fields.Selection(
        NAME_MONTH,
        'MES',
        required=True,
        store=True,
    )

    bussines_days = Integer(
        string= 'Dias Habiles',
        required=True,
        store = True,
    )

    year = Integer(
        string = 'Año',
        required= True,
        store = True,
    )
