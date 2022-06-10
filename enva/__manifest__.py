# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'ENVA App',
    'version': '12.0.1.0.0',
    "author": "Vauxoo",
    "license": "LGPL-3",
    'category': 'Hidden',
    'summary': 'ENVA App for customizations',
    'depends': [
        'l10n_mx_edi',
    ],
    'data': [
        "data/cfdi.xml",
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': True,
}
