# Copyright 2020 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
{
    'name': 'Addenda pepsico',
    'summary': '''
    Addenda for PepsiCo Mexico
    ''',
    'author': 'Vauxoo',
    'website': 'https://www.vauxoo.com',
    'license': 'LGPL-3',
    'category': 'Installer',
    'version': '14.0.1.0.0',
    'depends': [
        'l10n_mx_edi',
    ],
    'test': [
    ],
    'data': [
        'data/addenda.xml',
        'views/account_move.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
