# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


NAME_BANK=[
('BANCOMER','BANCOMER'),
('SANTANDER','SANTANDER'),
('MULTIVA','MULTIVA')
]

NAME_ACCOUNT=[
('SERVICIOS PENINSULARES INDUSTRIALES DEL SURESTE SA DE CV','SERVICIOS PENINSULARES INDUSTRIALES DEL SURESTE SA DE CV'),
('INDUSTRIAL CONSULTING SCP','INDUSTRIAL CONSULTING SCP'),
]

class BankBalance(models.Model):
    _name = 'bank.balance.nova'
    _description = "Bank Balance"

    
    name = fields.Date(
        string='Fecha',
        required=True,
        store = True,
    )
    
    bank = fields.Selection(
        NAME_BANK,
        'Banco',
        required=True,
        store=True,
    )
    
    account = fields.Selection(
        NAME_ACCOUNT,
        'Cuenta',
        required=True,
        store=True,
    )
    
    initial_balance = fields.Float(
        string="Balance Inicial",
        store=True,
    )
   
   