from odoo import api, fields, models

from ..hooks import _load_xsd_complement


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_isepi = fields.Boolean(
        string='Is an Electronic purse issuer?',
        help='This add the electronic purse emission complement for fuel '
        'consumption')

    @api.model
    def _load_xsd_attachments(self):
        # noqa TODO Remove after of this merge https://github.com/odoo/enterprise/pull/1617
        res = super(ResCompany, self)._load_xsd_attachments()
        # complemento de Estado de Cuenta de Combustible
        url = 'http://www.sat.gob.mx/sitio_internet/cfd/EstadoDeCuentaCombustible/ecc12.xsd'  # noqa
        namespace = 'http://www.sat.gob.mx/EstadoDeCuentaCombustible12'
        xsd = self.env.ref(
            'l10n_mx_edi.xsd_cached_ecc12_xsd', False)
        if xsd:
            xsd.unlink()
        _load_xsd_complement(self._cr, None, url, namespace)
        # complemento de Consumo de Combustibles
        url = 'http://www.sat.gob.mx/sitio_internet/cfd/ConsumoDeCombustibles/consumodeCombustibles11.xsd'  # noqa
        namespace = 'http://www.sat.gob.mx/ConsumoDeCombustibles11'
        xsd = self.env.ref(
            'l10n_mx_edi.xsd_cached_consumodeCombustibles11_xsd', False)
        if xsd:
            xsd.unlink()
        _load_xsd_complement(self._cr, None, url, namespace)
        return res
