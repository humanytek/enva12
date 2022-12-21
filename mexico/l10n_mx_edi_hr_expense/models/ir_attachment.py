# Copyright 2018, Vauxoo, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import logging
from io import BytesIO

from lxml import objectify
from odoo import api, models
from odoo.tools.xml_utils import _check_with_xsd
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.multi
    def l10n_mx_edi_is_expense(self):
        self.ensure_one()

        # Using sudo because we need to be as efficient as possible here
        # jumping the ACL process.
        if not self.sudo().res_model == 'hr.expense' and not \
                self.sudo().company_id.country_id == self.env.ref('base.mx'):
            return False
        return True

    @api.model
    def l10n_mx_edi_is_cfdi33(self):
        self.ensure_one()
        if not self.datas or not self.l10n_mx_edi_is_expense():
            return False
        try:
            datas = base64.b64decode(self.datas).replace(
                b'xmlns:schemaLocation', b'xsi:schemaLocation')
            objectify.fromstring(datas)
        except (SyntaxError, ValueError):
            return False

        attachment = self.env.ref('l10n_mx_edi.xsd_cached_cfdv33_xsd', False)
        schema = base64.b64decode(attachment.datas) if attachment else b''
        xml = datas or b''
        try:
            if objectify.fromstring(xml).get('Version') != '3.3':
                return False
            with BytesIO(schema) as xsd:
                _check_with_xsd(xml, xsd)
        except ValueError:
            return False
        except IOError:
            return False
        except UserError as e:

            # Ugly hack to use the xsd validation, the Timbre is not part of
            # The validation and give specifically this error:
            # >>
            # Element
            # '{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital
            #  No matching global element declaration available, but demanded
            #  by the strict wildcard
            # >>
            # That's why this ugly if, dear future me, I am really sorry.

            if "TimbreFiscalDigital" in e.name:
                # It is an xml, has the schema and is signed.
                # If this explode we need an explicit traceback
                # (may be a new case).
                cfdi = self.env['account.invoice'].l10n_mx_edi_get_tfd_etree(
                    objectify.fromstring(xml))
                uuid = cfdi.get('UUID') if cfdi is not None else False
                return uuid
            _logger.info('A cfdi was checked and give the error %s' % e.name)
            return False

        return False
