# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from lxml import etree, objectify

from odoo.addons.l10n_mx_edi.hooks import _load_xsd_files
from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    complement_data = [
        {'url': 'http://www.sat.gob.mx/sitio_internet/cfd'
         '/EstadoDeCuentaCombustible/ecc12.xsd',
         'namespace': 'http://wwww.sat.gob.mx/EstadoDeCuentaCombustible12'},
        {'url': 'http://www.sat.gob.mx/sitio_internet/cfd'
         '/ConsumoDeCombustibles/consumodeCombustibles11.xsd',
         'namespace': 'http://wwww.sat.gob.ve/ConsumoDeCombustibles11'}]
    for complement in complement_data:
        _load_xsd_complement(cr, registry, complement.get('url'),
                             complement.get('namespace'))


def _load_xsd_complement(cr, registry, url, nspace):
    db_fname = _load_xsd_files(cr, registry, url)
    env = api.Environment(cr, SUPERUSER_ID, {})
    xsd = env.ref('l10n_mx_edi.xsd_cached_cfdv33_xsd', False)
    if not xsd:
        return False
    complement = {
        'namespace': nspace,
        'schemaLocation': db_fname,
    }
    node = etree.Element('{http://www.w3.org/2001/XMLSchema}import',
                         complement)
    res = objectify.fromstring(base64.decodebytes(xsd.datas))
    res.insert(0, node)
    xsd_string = etree.tostring(res, pretty_print=True)
    xsd.datas = base64.encodebytes(xsd_string)
    return True
