# -*- coding: utf-8 -*-

from odoo import api, fields, models

from ..hooks import _load_xsd_complement


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_complement_type = fields.Selection(
        selection=[
            ('destruction', 'Destruction Certificate'),
            ('renew', 'Vehicle Renew and Substitution'),
            ('sale', 'Sale of vehicles'),
            ('pfic', 'Natural person member of the coordinated')
        ],
        string='Vehicle Complement',
        help='Select one of those complements if you want it to be available '
        'for invoice')

    @api.model
    def _load_xsd_attachments(self):
        # noqa TODO Remove after of this merge https://github.com/odoo/enterprise/pull/1617
        res = super(ResCompany, self)._load_xsd_attachments()
        # Certificado de Destruccion
        url = 'http://www.sat.gob.mx/sitio_internet/cfd/certificadodestruccion/certificadodedestruccion.xsd'  # noqa
        namespace = 'http://www.sat.gob.mx/certificadodestruccion'
        xsd = self.env.ref(
            'l10n_mx_edi.xsd_cached_certificadodedestruccion_xsd', False)
        if xsd:
            xsd.unlink()
        _load_xsd_complement(self._cr, None, url, namespace)
        # Vehiculo Usado
        url = 'http://www.sat.gob.mx/sitio_internet/cfd/vehiculousado/vehiculousado.xsd'  # noqa
        namespace = 'http://www.sat.gob.mx/vehiculousado'
        xsd = self.env.ref(
            'l10n_mx_edi.xsd_cached_vehiculousado', False)
        if xsd:
            xsd.unlink()
        _load_xsd_complement(self._cr, None, url, namespace)
        # Renovacion y sustutucion de vehiculos
        url = 'http://www.sat.gob.mx/sitio_internet/cfd/renovacionysustitucionvehiculos/renovacionysustitucionvehiculos.xsd' # noqa
        namespace = 'http://wwww.sat.gob.mx/renovacionysustitucionvehiculos'
        xsd = self.env.ref(
            'l10n_mx_edi.xsd_cached_renovacionysustitucionvehiculos', False)
        if xsd:
            xsd.unlink()
        _load_xsd_complement(self._cr, None, url, namespace)
        # Persona fisica integrante de coordinados
        url = 'http://www.sat.gob.mx/sitio_internet/cfd/pfic/pfic.xsd'
        namespace = 'http://wwww.sat.gob.mx/pfic'
        xsd = self.env.ref('l10n_mx_edi.xsd_cached_pfic', False)
        if xsd:
            xsd.unlink()
        _load_xsd_complement(self._cr, None, url, namespace)
        return res
