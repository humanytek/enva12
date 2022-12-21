# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo Mexico Localization Customs for DIOT',
    'version': '12.0.1.0.0',
    'author': 'Vauxoo',
    'category': 'Accounting',
    'license': 'OEEL-1',
    'depends': [
        'account',
        'l10n_mx_edi_customs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/customs_view.xml',
        'views/account_invoice_view.xml',
        'views/res_partner_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
}
