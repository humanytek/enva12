from odoo import api, models

from ..hooks import _load_xsd_complement


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _load_xsd_attachments(self):
        # noqa TODO Remove after of this merge https://github.com/odoo/enterprise/pull/1617
        res = super(ResCompany, self)._load_xsd_attachments()
        url = 'http://www.sat.gob.mx/sitio_internet/cfd/notariospublicos/notariospublicos.xsd' # noqa
        namespaces = 'http://www.sat.gob.mx/notariospublicos'
        xsd = self.env.ref(
            'l10n_mx_edi.xsd_cached_notariospublicos_xsd', False)
        if xsd:
            xsd.unlink()
        _load_xsd_complement(self._cr, None, url, namespaces)
        return res
