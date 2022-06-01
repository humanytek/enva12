# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import Warning, UserError
from odoo.tools.float_utils import float_compare, float_repr
from odoo.exceptions import ValidationError, UserError

import base64
import requests

from lxml import etree
from lxml.objectify import fromstring
from pytz import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta


CFDI_XSLT_CADENA = 'l10n_mx_edi/data/3.3/cadenaoriginal.xslt'
CFDI_XSLT_CADENA_TFD = 'l10n_mx_edi/data/xslt/3.3/cadenaoriginal_TFD_1_1.xslt'

class Account_invoice_nova(models.Model):
    _inherit = 'account.move'


    type_currency = fields.Monetary(
        digits = (8,6),
        # string='Type Currency',
        compute='_get_type_currency',


    )


    transfer_ids=fields.Many2many(
    comodel_name='stock.picking',
    relation='invoice_transfer_rel',
    column1='account_invoice_id',
    column2='stock_picking_id',
    store=True,
    )

    re_facturado=fields.Boolean(
    string='Re-Facturado',
    store=True,
    copy=False
    )

    facturado_to=fields.Boolean(
    string='Facturado a:',
    store=True,
    copy=False
    )

    not_accumulate=fields.Boolean(
    string='No Acumular',
    store=True,
    default=False,
    copy=False
    )

    date_applied = fields.Date(
        string='Fecha Aplicada',
        store=True,
        index=True,
        copy=False)

    cfdi_uuid_enva = fields.Char(
        string='Folio Fiscal',
        store=True,
        copy=False
    )

    def _post(self, soft=True):

        self.write({'date_applied': fields.Date.context_today(self)})

        return super()._post(soft=soft)


    @api.depends('amount_total_signed', 'amount_total')
    def _get_type_currency(self):
        for r in self:
            if r.amount_total_signed > 0 and r.amount_total > 0:
                r.type_currency = r.amount_total_signed / r.amount_total
            else:
                r.type_currency = 0


    # def _l10n_mx_edi_decode_cfdi(self, cfdi_data=None):
    #     ''' Helper to extract relevant data from the CFDI to be used, for example, when printing the invoice.
    #     :param cfdi_data:   The optional cfdi data.
    #     :return:            A python dictionary.
    #     '''
    #     self.ensure_one()
    #
    #     def get_node(cfdi_node, attribute, namespaces):
    #         if hasattr(cfdi_node, 'Complemento'):
    #             node = cfdi_node.Complemento.xpath(attribute, namespaces=namespaces)
    #             return node[0] if node else None
    #         else:
    #             return None
    #
    #     def get_cadena(cfdi_node, template):
    #         if cfdi_node is None:
    #             return None
    #         cadena_root = etree.parse(tools.file_open(template))
    #         return str(etree.XSLT(cadena_root)(cfdi_node))
    #
    #     # Find a signed cfdi.
    #     if not cfdi_data:
    #         signed_edi = self._get_l10n_mx_edi_signed_edi_document()
    #         if signed_edi:
    #             cfdi_data = base64.decodebytes(signed_edi.attachment_id.with_context(bin_size=False).datas)
    #
    #     # Nothing to decode.
    #     if not cfdi_data:
    #         return {}
    #
    #     cfdi_node = fromstring(cfdi_data)
    #     tfd_node = get_node(
    #         cfdi_node,
    #         'tfd:TimbreFiscalDigital[1]',
    #         {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'},
    #     )
    #
    #     return {
    #         'uuid': ({} if tfd_node is None else tfd_node).get('UUID'),
    #         'supplier_rfc': cfdi_node.Emisor.get('Rfc', cfdi_node.Emisor.get('rfc')),
    #         'customer_rfc': cfdi_node.Receptor.get('Rfc', cfdi_node.Receptor.get('rfc')),
    #         'id_fiscal': cfdi_node.Receptor.get('NumRegIdTrib'),
    #         'currency_type': cfdi_node.Receptor.get('TipoCambio'),
    #         'amount_total': cfdi_node.get('Total', cfdi_node.get('total')),
    #         'cfdi_node': cfdi_node,
    #         'usage': cfdi_node.Receptor.get('UsoCFDI'),
    #         'payment_method': cfdi_node.get('formaDePago', cfdi_node.get('MetodoPago')),
    #         'bank_account': cfdi_node.get('NumCtaPago'),
    #         'sello': cfdi_node.get('sello', cfdi_node.get('Sello', 'No identificado')),
    #         'sello_sat': tfd_node is not None and tfd_node.get('selloSAT', tfd_node.get('SelloSAT', 'No identificado')),
    #         'cadena': tfd_node is not None and get_cadena(tfd_node, CFDI_XSLT_CADENA_TFD) or get_cadena(cfdi_node, CFDI_XSLT_CADENA),
    #         'certificate_number': cfdi_node.get('noCertificado', cfdi_node.get('NoCertificado')),
    #         'certificate_sat_number': tfd_node is not None and tfd_node.get('NoCertificadoSAT'),
    #         'expedition': cfdi_node.get('LugarExpedicion'),
    #         'fiscal_regime': cfdi_node.Emisor.get('RegimenFiscal', ''),
    #         'emission_date_str': cfdi_node.get('fecha', cfdi_node.get('Fecha', '')).replace('T', ' '),
    #         'stamp_date': tfd_node is not None and tfd_node.get('FechaTimbrado', '').replace('T', ' '),
    #     }
    #     return super()._l10n_mx_edi_decode_cfdi(self, cfdi_data=None)
