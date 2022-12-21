# -*- coding: utf-8 -*-

from odoo import api, fields, models

from ..hooks import _load_xsd_complement


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_donat_auth = fields.Char(
        'Authorization Number', help='Number of document on which is '
        'informed the civil organization or escrow, the procedence of the '
        'authorization to receive deductible donations, or its corresponding '
        'renovation granted by SAT')
    l10n_mx_edi_donat_date = fields.Date(
        'Authorization Date', help='Date of document on which is '
        'informed the civil organization or escrow, the procedence of the '
        'authorization to receive deductible donations, or its corresponding '
        'renovation granted by SAT')
    l10n_mx_edi_donat_note = fields.Text(
        'Note', help='Field to prove the voucher issued is derived '
        'from a donation')

    @api.model
    def _load_xsd_attachments(self):
        res = super(ResCompany, self)._load_xsd_attachments()
        url = 'http://www.sat.gob.mx/sitio_internet/cfd/donat/donat11.xsd'
        xsd = self.env.ref(
            'l10n_mx_edi.xsd_cached_donat11_xsd', False)
        if xsd:
            xsd.unlink()
        _load_xsd_complement(self._cr, None, url)
        return res
