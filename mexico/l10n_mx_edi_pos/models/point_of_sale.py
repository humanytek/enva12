# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from __future__ import division

import base64
import logging
from io import BytesIO

from lxml import etree, objectify
from suds.client import Client

from odoo import _, api, fields, models
from odoo.tools import float_round
from odoo.addons.l10n_mx_edi.models.account_invoice import create_list_html
from odoo.exceptions import UserError
from odoo.tools import config
from odoo.tools.safe_eval import safe_eval
from odoo.tools.xml_utils import _check_with_xsd

_logger = logging.getLogger(__name__)

CFDI_TEMPLATE_33 = 'l10n_mx_edi_pos.cfdiv33_pos'
CFDI_XSLT_CADENA = 'l10n_mx_edi/data/3.3/cadenaoriginal.xslt'


class PosSession(models.Model):
    _name = 'pos.session'
    _inherit = ['pos.session', 'mail.thread']

    l10n_mx_edi_pac_status = fields.Selection(
        selection=[
            ('retry', 'Retry'),
            ('signed', 'Signed'),
            ('to_cancel', 'To cancel'),
            ('cancelled', 'Cancelled')
        ],
        string='PAC status',
        help='Refers to the status of the invoice inside the PAC.',
        readonly=True,
        copy=False)

    @api.multi
    def l10n_mx_edi_update_pac_status(self):
        """Synchronize both systems: Odoo & PAC if the invoices need to be
        signed or cancelled.
        """
        for record in self:
            if record.l10n_mx_edi_pac_status == 'to_cancel':
                record.l10n_mx_edi_cancel()
            elif record.l10n_mx_edi_pac_status in ['retry', 'cancelled']:
                record._l10n_mx_edi_retry()

    @api.multi
    def _l10n_mx_edi_retry(self):
        """Generate and sign CFDI with version 3.3, just for the next cases:
        1.- The order was generated without customer, therefore without invoice
        2.- The order was generated with customer, but without invoice."""
        self.ensure_one()
        orders = self.order_ids.filtered(
            lambda r: not r.invoice_id and not r.xml_generated)
        # skip orders with a refund related
        skip_orders = orders.filtered(
            lambda r: (r.amount_total < 0 and not r._get_order_related()
                       .l10n_mx_edi_uuid) or (
                           r.amount_total > 0 and r ._get_order_related()
                           .session_id.state == 'closed'))
        orders -= skip_orders
        if skip_orders:
            olist = ' '.join(['<li>%s</li>' % (o) for o in skip_orders.mapped(
                'pos_reference')])
            msg_body = _("""The following orders were skipped because it's not
                         necessary to sign them:
                         <br><br><ul>%s</ul>""") % olist
            self.message_post(body=msg_body)
        partners = orders.mapped('partner_id').mapped(
            'commercial_partner_id').filtered(lambda r: r.vat)
        lambda_functions = (
            lambda r: r.amount_total > 0 and  # Order with partner
            r.partner_id and r.partner_id.commercial_partner_id.id
            not in partners.ids,
            lambda r: r.amount_total > 0 and not  # Order without Partner
            r.partner_id,
            lambda r: r.amount_total < 0 and  # Refund with partner
            r.partner_id and r.partner_id.commercial_partner_id.id
            not in partners.ids,
            lambda r: r.amount_total < 0 and not  # Refund without Partner
            r.partner_id)
        signed = []
        self.l10n_mx_edi_pac_status = 'retry'
        attachment = self.env['ir.attachment']
        for func in lambda_functions:
            order_filter = orders.filtered(func)
            if not order_filter:
                continue
            cfdi_values = order_filter._l10n_mx_edi_create_cfdi()
            error = cfdi_values.pop('error', None)
            cfdi = cfdi_values.pop('cfdi', None)
            if error:
                self.message_post(body=error)
                signed.append(False)
                continue

            filename = order_filter.get_file_name()
            ctx = self.env.context.copy()
            ctx.pop('default_type', False)
            attachment_id = attachment.with_context(ctx).create({
                'name': '%s.xml' % filename,
                'res_id': self.id,
                'res_model': self._name,
                'datas': base64.encodestring(cfdi),
                'datas_fname': '%s.xml' % filename,
                'description': _('Mexican PoS'),
                })
            self.message_post(
                body=_('CFDI document generated (may be not signed)'),
                attachment_ids=[attachment_id.id],
                subtype='account.mt_invoice_validated')

            cfdi_values = self._l10n_mx_edi_call_service('sign', cfdi)
            if cfdi_values:
                self._l10n_mx_edi_post_sign_process(cfdi_values, order_filter)
                signed.append(bool(cfdi_values.get('cfdi', False)))
            orders = orders - order_filter
        if all(signed):
            self.l10n_mx_edi_pac_status = 'signed'

    @api.multi
    def _l10n_mx_edi_call_service(self, service_type, cfdi):
        """Call the right method according to the pac_name,
        it's info returned by the '_l10n_mx_edi_%s_info' % pac_name'
        method and the service_type passed as parameter.
        :param service_type: sign or cancel
        :type service_type: str
        :param cfdi: fiscal document
        :type cfdi: etree
        :return: the Result of the service called
        :rtype: dict
        """
        self.ensure_one()
        invoice_obj = self.env['account.invoice']
        company_id = self.config_id.company_id
        pac_name = company_id.l10n_mx_edi_pac
        if not pac_name:
            return False
        # Get the informations about the pac
        pac_info_func = '_l10n_mx_edi_%s_info' % pac_name
        service_func = '_l10n_mx_edi_%s_%s' % (pac_name, service_type)
        pac_info = getattr(
            invoice_obj, pac_info_func)(company_id, service_type)
        return getattr(self, service_func)(pac_info, cfdi)

    @api.multi
    def l10n_mx_edi_log_error(self, message):
        self.message_post(body=_('Error during the process: %s') % message,
                          subtype='account.mt_invoice_validated')

    @api.multi
    def _l10n_mx_edi_post_sign_process(self, cfdi_values, order_ids):
        """Post process the results of the sign service.
        :param cfdi_values: info of xml signed
        :type cfdi_values: dict
        :param order_ids: orders use to generate cfdi
        :type order_ids: pos.order
        """
        self.ensure_one()
        post_msg = []
        attach = []
        invoice_obj = self.env['account.invoice']
        xml_signed = cfdi_values.get('cfdi', '')
        code = cfdi_values.get('code', '')
        msg = cfdi_values.get('error', '')
        filename = order_ids.get_file_name()
        if xml_signed:
            body_msg = _('The sign service has been called with '
                         'success to %s') % filename
            # attach cfdi
            ctx = self.env.context.copy()
            ctx.pop('default_type', False)
            attachment_id = self.l10n_mx_edi_retrieve_last_attachment(
                '%s.xml' % filename)
            attachment_id.write({
                'datas': xml_signed,
                'datas_fname': '%s.xml' % filename,
                'description': 'Mexican invoice',
            })
            attach.extend([attachment_id.id])
            # Generate and attach pdf
            report = self.env.ref('l10n_mx_edi_pos.l10n_mx_edi_report_session')
            xml = objectify.fromstring(base64.b64decode(xml_signed))
            data = {'cfdi': xml}
            # The generation of report does not work in test environment
            # because of this issue https://github.com/odoo/odoo/issues/18841
            if not config['test_enable']:
                pdf, ext = report.render_qweb_pdf(self.ids, data)
                attachment_id = self.env[
                    'ir.attachment'].with_context(ctx).create({
                        'name': '%s.%s' % (filename, ext),
                        'res_id': self.id,
                        'res_model': self._name,
                        'datas': base64.b64encode(pdf),
                        'datas_fname': '%s.pdf' % filename,
                        'description': 'Printed representation of the CFDI',
                    })
                attach.extend([attachment_id.id])
            uuid = invoice_obj.l10n_mx_edi_get_tfd_etree(xml).get('UUID', '')
            order_ids.write({'xml_generated': True, 'l10n_mx_edi_uuid': uuid})
        else:
            body_msg = _('The sign service requested failed to %s') % filename
        if code:
            post_msg.extend([_('Code: ') + str(code)])
        if msg:
            post_msg.extend([_('Message: ') + msg])
        self.message_post(
            body=body_msg + create_list_html(post_msg),
            attachment_ids=attach,
            subtype='account.mt_invoice_validated')

    @api.multi
    def _l10n_mx_edi_post_cancel_process(self, cfdi_values, order_ids, attach):
        """Post process the results of the cancel service.
        :param cfdi_values: info of xml signed
        :type cfdi_values: dict
        :param order_ids: orders use to generate cfdi
        :type order_ids: pos.order
        :param attach: file attachment in invoice
        :type attach: ir.attachment
        """

        self.ensure_one()
        cancelled = cfdi_values.get('cancelled', '')
        code = cfdi_values.get('code', '')
        msg = cfdi_values.get('msg', '')
        filename = cfdi_values.get('filename', '')
        if cancelled:
            body_msg = _('The cancel service has been called with success '
                         'to %s') % filename
            order_ids.write({'xml_generated': False})
            attach.name = 'cancelled_%s' % '_'.join(
                filename.split('_')[-2:])
        else:
            body_msg = _(
                'The cancel service requested failed to %s') % filename
        post_msg = []
        if code:
            post_msg.extend([_('Code: ') + str(code)])
        if msg:
            post_msg.extend([_('Message: ') + msg])
        self.message_post(
            body=body_msg + create_list_html(post_msg),
            subtype='account.mt_invoice_validated')

    @api.multi
    def action_pos_session_close(self):
        orders = self.order_ids.filtered(
            lambda r:
            not r.invoice_id and not r.xml_generated and r.partner_id and
            r.partner_id.vat)
        orders.action_create_invoice()
        orders.action_validate_invoice()
        res = super(PosSession, self).action_pos_session_close()
        self._l10n_mx_edi_retry()
        return res

    @api.multi
    def l10n_mx_edi_cancel(self):
        """If the session have XML documents, try send to cancel in SAT system
        """
        att_obj = self.env['ir.attachment']
        for record in self:
            attach_xml_ids = att_obj.search([
                ('name', 'ilike', '%s%%.xml' % record.name.replace('/', '_')),
                ('res_model', '=', record._name),
                ('res_id', '=', record.id),
            ])
            cancel = []
            self.l10n_mx_edi_pac_status = 'to_cancel'
            for att in attach_xml_ids.filtered('datas'):
                cfdi_values = self._l10n_mx_edi_call_service(
                    'cancel', att.datas)
                if not cfdi_values:
                    cancel.append([False])
                    continue
                orders = self.order_ids.filtered(
                    lambda r: not r.invoice_id and r.xml_generated)
                func = (lambda r: r.partner_id) if _(
                    'with_partner') in att.name else (
                        lambda r: not r.partner_id)
                order_ids = orders.filtered(func)
                cfdi_values.update({'filename': att.name})
                self._l10n_mx_edi_post_cancel_process(
                    cfdi_values, order_ids, att)
                cancel.append(cfdi_values.get('cancelled', False))
            if all(cancel):
                self.l10n_mx_edi_pac_status = 'cancelled'

    # -------------------------------------------------------------------------
    # SAT/PAC service methods
    # -------------------------------------------------------------------------

    @api.multi
    def _l10n_mx_edi_solfact_sign(self, pac_info, cfdi):
        """SIGN for Solucion Factible.
        """
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        cfdi = base64.b64encode(cfdi).decode('UTF-8')
        try:
            client = Client(url, timeout=20)
            response = client.service.timbrar(username, password, cfdi, False)
        except BaseException as e:
            return {'error': 'Error during the process', 'code': str(e)}
        res = response.resultados
        msg = getattr(res[0] if res else response, 'mensaje', None)
        code = getattr(res[0] if res else response, 'status', None)
        xml_signed = getattr(res[0] if res else response, 'cfdiTimbrado', None)
        if xml_signed:
            return {'cfdi': xml_signed}
        return {'error': msg, 'code': code}

    @api.multi
    def _l10n_mx_edi_solfact_cancel(self, pac_info, cfdi):
        """CANCEL for Solucion Factible.
        """
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        invoice_obj = self.env['account.invoice']
        xml_string = base64.b64decode(cfdi)
        xml = objectify.fromstring(xml_string)
        uuids = [invoice_obj.l10n_mx_edi_get_tfd_etree(xml).get('UUID', '')]
        company_id = self.config_id.company_id
        certificate_ids = company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        cer_pem = base64.b64encode(certificate_id.get_pem_cer(
            certificate_id.content)).decode('UTF-8')
        key_pem = base64.b64encode(certificate_id.get_pem_key(
            certificate_id.key, certificate_id.password)).decode('UTF-8')
        key_password = certificate_id.password
        try:
            client = Client(url, timeout=20)
            response = client.service.cancelar(username, password, uuids,
                                               cer_pem, key_pem, key_password)
        except BaseException as e:
            self.l10n_mx_edi_log_error(str(e))
            return {}
        res = response.resultados
        code = getattr(res[0], 'statusUUID', None) if res else getattr(
            response, 'status', None)
        cancelled = code in ('201', '202')  # cancelled or previously cancelled
        # no show code and response message if cancel was success
        msg = '' if cancelled else getattr(
            res[0] if res else response, 'mensaje', None)
        code = '' if cancelled else code
        return {'cancelled': cancelled, 'code': code, 'msg': msg}

    @api.multi
    def _l10n_mx_edi_finkok_sign(self, pac_info, cfdi):
        """SIGN for Finkok.
        """
        # TODO - Same method that on invoice
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        cfdi = [base64.b64encode(cfdi).decode('UTF-8')]
        try:
            client = Client(url, timeout=20)
            response = client.service.stamp(cfdi, username, password)
        except BaseException as e:
            return {'error': 'Error during the process', 'code': str(e)}
        code = 0
        msg = None
        if response.Incidencias:
            code = getattr(response.Incidencias[0][0], 'CodigoError', None)
            msg = getattr(
                response.Incidencias[0][0], 'MensajeIncidencia', None)
            return {'error': msg, 'code': code}

        xml_signed = getattr(response, 'xml', None)
        xml_signed = base64.b64encode(xml_signed.encode('utf-8'))
        return {'cfdi': xml_signed}

    @api.multi
    def _l10n_mx_edi_finkok_cancel(self, pac_info, cfdi):
        """CANCEL for Finkok.
        """
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        invoice_obj = self.env['account.invoice']
        xml_string = base64.b64decode(cfdi)
        xml = objectify.fromstring(xml_string)
        uuid = invoice_obj.l10n_mx_edi_get_tfd_etree(xml).get('UUID', '')
        if not uuid:
            return {}
        company_id = self.config_id.company_id
        certificate_ids = company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        cer_pem = base64.b64encode(certificate_id.get_pem_cer(
            certificate_id.content)).decode('UTF-8')
        key_pem = base64.b64encode(certificate_id.get_pem_key(
            certificate_id.key, certificate_id.password)).decode('UTF-8')
        cancelled = False
        code = False
        try:
            client = Client(url, timeout=20)
            invoices_list = client.factory.create("UUIDS")
            invoices_list.uuids.string = [uuid]
            response = client.service.cancel(
                invoices_list, username, password, company_id.vat,
                cer_pem, key_pem)
        except BaseException as e:
            self.l10n_mx_edi_log_error(str(e))
            return {}
        if not getattr(response, 'Folios', None):
            code = getattr(response, 'CodEstatus', None)
            msg = _("Cancelling got an error") if code else _(
                'A delay of 2 hours has to be respected before to cancel')
        else:
            code = getattr(response.Folios[0][0], 'EstatusUUID', None)
            # cancelled or previously cancelled
            cancelled = code in ('201', '202')
            # no show code and response message if cancel was success
            code = '' if cancelled else code
            msg = '' if cancelled else _("Cancelling got an error")
        return {'cancelled': cancelled, 'code': code, 'msg': msg}

    @api.model
    def l10n_mx_edi_retrieve_attachments(self, filename):
        """Retrieve all the cfdi attachments generated for this session
        :return: An ir.attachment recordset
        :rtype: ir.attachment()
        """
        self.ensure_one()
        domain = [
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('name', '=', filename)]
        return self.env['ir.attachment'].search(domain)

    @api.model
    def l10n_mx_edi_retrieve_last_attachment(self, filename):
        attachment_ids = self.l10n_mx_edi_retrieve_attachments(filename)
        return attachment_ids[0] if attachment_ids else None


class PosOrder(models.Model):

    _inherit = 'pos.order'

    xml_generated = fields.Boolean(
        'XML Generated', copy=False,
        help='Indicate if this order was consider in the session XML')
    l10n_mx_edi_uuid = fields.Char(
        'Fiscal Folio', copy=False, index=True,
        help='Folio in electronic document, returned by SAT.',)

    def _get_order_related(self):
        self.ensure_one()
        return self.search([
            ('pos_reference', '=', self.pos_reference), ('id', '!=', self.id),
            ('partner_id', '=', self.partner_id.id)], limit=1)

    @api.multi
    def get_file_name(self):
        """Return the file name, with a consecutive to duplicated names.
        Params:
            partner: Receive True if the file to generate contain the records
            that have partner reference, to set in the fail the label
            'with_partner'
            inc: Indicate if must be add the consecutive"""
        partner = self.mapped('partner_id')
        doc_type = self.filtered(lambda r: r.amount_total < 0)
        type_rec = _('with_partner') if partner else _('wo_partner')
        egre = '' if not doc_type else _('_refund')
        session = self.mapped('session_id')
        session_name = session.name.replace('/', '_')
        fname = "%s_%s%s" % (session_name, type_rec, egre)

        count = self.env['ir.attachment'].search_count([
            ('name', '=', fname),
            ('res_model', '=', session._name),
            ('res_id', '=', session.id),
        ])
        if count > 0:
            fname = "%s_%s%s_%s" % (
                session_name, type_rec, egre, count + 1)
        return fname

    def _get_subtotal_wo_discount(self, precision_digits, line):
        return float_round(
            abs(line.price_subtotal) / (1 - abs(line.discount/100))
            if line.discount != 100 else abs(line.price_unit * line.qty),
            int(precision_digits))

    def _get_discount(self, precision_digits, line):
        return float(('%.*f' % (int(precision_digits),
                                self._get_subtotal_wo_discount(
                                    precision_digits, line) -
                                abs(line.price_subtotal)))
                     if line.discount else False)

    @api.multi
    def _l10n_mx_edi_create_cfdi_values(self):
        """Generating the base dict with data needed to generate the electronic
        document
        :return: Base data to generate electronic document
        :rtype: dict
        """
        session = self.mapped('session_id')
        invoice_obj = self.env['account.invoice']
        precision_digits = self.env[
            'decimal.precision'].precision_get('Account')
        company_id = session.config_id.company_id

        invoice = {
            'record': self,
            'invoice': invoice_obj,
            'currency': session.currency_id.name,
            'supplier': company_id.partner_id.commercial_partner_id,
            'folio': session.name,
            'serie': 'NA',
            'decimal_precision': precision_digits,
        }
        invoice['subtotal_wo_discount'] = sum([
            self._get_subtotal_wo_discount(precision_digits, l) for l in
            self.mapped('lines')])
        invoice['amount_untaxed'] = '%.*f' % (precision_digits, sum(
            [self._get_subtotal_wo_discount(precision_digits, p) for p in
             self.mapped('lines')]))
        invoice['amount_discount'] = sum([
            float(self._get_discount(precision_digits, p)) for p in
            self.mapped('lines')])

        invoice['tax_name'] = lambda t: {
            'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(t, False)
        invoice['taxes'] = self._l10n_mx_edi_create_taxes_cfdi_values()

        invoice['amount_total'] = '%0.*f' % (
            precision_digits, float(invoice['amount_untaxed']) - float(
                invoice['amount_discount'] or 0) + (
                    invoice['taxes']['total_transferred'] or 0) - (
                        invoice['taxes']['total_withhold'] or 0))
        invoice['document_type'] = 'I' if float(
            invoice['amount_total']) > 0 else 'E'
        return invoice

    @api.multi
    def get_cfdi_related(self):
        """To node CfdiRelacionados get documents related with that order
        Considered:
            - Order Refund
            - Order Cancelled"""
        cfdi_related = []
        refund = self.filtered(
            lambda a: a.amount_total < 0 and not a.l10n_mx_edi_uuid)
        relation_type = '04' if self[0].l10n_mx_edi_uuid else (
            '01' if refund else '')
        for order in refund:
            origin = self.search(
                [('pos_reference', '=', order.pos_reference),
                 ('id', '!=', order.id),
                 ('partner_id', '=', order.partner_id.id),
                 ('date_order', '<=', order.date_order)], limit=1)
            cfdi_related += [origin.l10n_mx_edi_uuid] if origin else ()
        cfdi_related += [
            i.l10n_mx_edi_uuid for i in self if i.l10n_mx_edi_uuid]
        if not cfdi_related:
            return {}
        return {
            'type': relation_type,
            'related': [x for x in set(cfdi_related)],
            }

    @api.multi
    def _l10n_mx_edi_create_cfdi(self):
        """Creates and returns a dictionnary containing 'cfdi' if the cfdi is
        well created, 'error' otherwise."""
        if not self:
            return {}
        qweb = self.env['ir.qweb']
        invoice_obj = self.env['account.invoice']
        company_id = self.mapped('company_id')
        error_log = []
        pac_name = company_id.l10n_mx_edi_pac

        values = self._l10n_mx_edi_create_cfdi_values()

        # -Check certificate
        certificate_ids = company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        if not certificate_id:
            error_log.append(_('No valid certificate found'))

        # -Check PAC
        if pac_name:
            pac_test_env = company_id.l10n_mx_edi_pac_test_env
            pac_username = company_id.l10n_mx_edi_pac_username
            pac_password = company_id.l10n_mx_edi_pac_password
            if not pac_test_env and not (pac_username and pac_password):
                error_log.append(_('No PAC credentials specified.'))
        else:
            error_log.append(_('No PAC specified.'))

        if error_log:
            return {'error': _('Please check your configuration: ') +
                    create_list_html(error_log)}

        values['certificate_number'] = certificate_id.serial_number
        values['certificate'] = certificate_id.sudo().get_data()[0]
        values['date'] = (certificate_id.sudo().get_mx_current_datetime().
                          strftime('%Y-%m-%dT%H:%M:%S'))

        cfdi = qweb.render(CFDI_TEMPLATE_33, values=values)
        attachment = self.env.ref('l10n_mx_edi.xsd_cached_cfdv33_xsd', False)
        xsd_datas = base64.b64decode(attachment.datas) if attachment else b''
        # -Compute cadena
        tree = objectify.fromstring(cfdi)
        cadena = invoice_obj.l10n_mx_edi_generate_cadena(
            CFDI_XSLT_CADENA, tree)
        tree.attrib['Sello'] = certificate_id.sudo().get_encrypted_cadena(
            cadena)

        # Check with xsd
        if xsd_datas:
            try:
                with BytesIO(xsd_datas) as xsd:
                    _check_with_xsd(tree, xsd)
            except (IOError, ValueError):
                _logger.info(_('The xsd file to validate the XML structure '
                               'was not found'))
            except BaseException as e:
                return {'error': (_('The cfdi generated is not valid') +
                                  create_list_html(str(e).split('\\n')))}

        return {'cfdi': etree.tostring(
            tree, pretty_print=True, xml_declaration=True, encoding='UTF-8')}

    @api.multi
    def _l10n_mx_edi_create_taxes_cfdi_values(self):
        """Create the taxes values to fill the CFDI template.
        """
        values = {
            'total_withhold': 0,
            'total_transferred': 0,
            'withholding': [],
            'transferred': [],
        }
        taxes = {}
        for line in self.mapped('lines').filtered('price_subtotal'):
            price = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
            tax_line = {tax['id']: tax for
                        tax in line.tax_ids_after_fiscal_position.compute_all(
                            price, line.order_id.pricelist_id.currency_id,
                            abs(line.qty), line.product_id,
                            line.order_id.partner_id)['taxes']}
            for tax in line.tax_ids_after_fiscal_position.filtered(
                    lambda r: r.l10n_mx_cfdi_tax_type != 'Exento'):
                tax_dict = tax_line.get(tax.id, {})
                amount = round(
                    abs(tax_dict.get('amount', tax.amount / 100 * float(
                        "%.2f" % line.price_subtotal))), 2)
                rate = round(abs(tax.amount), 2)
                base = float(amount) / float(
                    rate) if tax.amount_type == 'fixed' else abs(tax_dict.get(
                        'base', line.price_subtotal))
                if tax.amount not in taxes:
                    taxes.update({tax.amount: {
                        'name': (tax.tag_ids[0].name
                                 if tax.tag_ids else tax.name).upper(),
                        'amount': amount,
                        'rate': (rate if tax.amount_type == 'fixed' else
                                 rate / 100.0),
                        'type': tax.l10n_mx_cfdi_tax_type,
                        'tax_amount': tax_dict.get('amount', tax.amount),
                        'base': base,
                    }})
                else:
                    taxes[tax.amount].update({
                        'amount': taxes[tax.amount]['amount'] + amount,
                        'base': taxes[tax.amount]['base'] + base,
                    })
                if tax.amount >= 0:
                    values['total_transferred'] += amount
                else:
                    values['total_withhold'] += amount
        values['transferred'] = [tax for tax in taxes.values() if tax[
            'tax_amount'] >= 0]
        values['withholding'] = [tax for tax in taxes.values() if tax[
            'tax_amount'] < 0]
        return values

    @api.multi
    def action_create_invoice(self):
        """When is created a new register, verify that partner have VAT, and
        create automatically the invoice."""
        for order in self:
            if order.partner_id.vat and not order.invoice_id:
                order.action_pos_order_invoice()

    @api.multi
    def action_validate_invoice(self):
        """Validate the invoice after of opened."""
        self.mapped('invoice_id').action_invoice_open()

    @api.multi
    def action_pos_order_paid(self):
        """Create Invoice if have partner with VAT"""
        res = super(PosOrder, self).action_pos_order_paid()
        self.action_create_invoice()
        self.filtered(
            lambda r: r.invoice_id.state == 'draft').action_validate_invoice()
        return res

    def _get_main_order(self):
        """Used to get the main order that generated the return that you want
        to generate the invoice
        :return: The possible order that generated the return
        :rtype: pos.order()
        """
        self.ensure_one()
        return self.search([
            ('partner_id', '=', self.partner_id.id),
            ('sale_journal', '=', self.sale_journal.id),
            ('invoice_id', '!=', False),
            ('pos_reference', '=', self.pos_reference),
        ], order='date_order DESC', limit=1)

    @api.multi
    def prepare_credit_note(self):
        """Prepare the main values needed to create the credit note
        :return: The values of the new invoice
        :rtype: dict
        """
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_('Please provide a partner for the sale.'))
        return {
            'name': self.name,
            'origin': self.name,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'journal_id': self.sale_journal.id or None,
            'type': 'out_refund',
            'reference': self.name,
            'partner_id': self.partner_id.id,
            'comment': self.note or '',
            'currency_id': self.pricelist_id.currency_id.id,
            'company_id': self.company_id.id,
        }

    @api.multi
    def prepare_invoice_line(self, line):
        """Prepare the values for create an invoice_line
        :param line: Line of the order used to create the invoice line
        :type line: pos.order.line()
        :return: The values required to create a line
        :rtype: dict
        """
        self.ensure_one()
        return {
            'product_id': line.product_id.id,
            'quantity': abs(line.qty),
            'account_analytic_id': self._prepare_analytic_account(line),
            'name': line.product_id.name_get()[0][1],
            'price_unit': line.price_unit,
            'discount': line.discount
        }

    @api.multi
    def create_refund_from_existing_invoice(self):
        """Generate a credit note from an existing invoice with the wizard
        located in the invoice view
        :return: The new credit note generated
        :rtype: dict
        """
        self.ensure_one()
        date_mx = fields.Datetime.context_timestamp(
            self.with_context(tz='America/Mexico_City'),
            fields.Datetime.from_string(fields.Datetime.now()))
        main_order = self._get_main_order()
        if main_order.invoice_id.state not in ('paid', 'open'):
            return False
        invoice = main_order.invoice_id
        self.state = 'invoiced'
        if invoice.state == 'paid':
            journals = invoice.move_id.line_ids.filtered("reconciled")
            journals.sudo().remove_move_reconcile()
        refund_id = self.env['account.invoice.refund'].with_context(
            active_id=invoice.id, active_ids=[invoice.id],
            active_model='account.invoice').create({
                'filter_refund': 'cancel',
                'description': self.name,
                'date_invoice': date_mx,
            })
        action = refund_id.invoice_refund()
        for item in action.get('domain') or []:
            if len(item) == 3 and item[0] == 'id':
                self.invoice_id = (
                    item[2][0] if isinstance(
                        item[2], (list, tuple)) else item[2])
                break
        return action

    @api.multi
    def create_credit_note(self):
        """Generate a credit note for a return of products
        :return: Action to show the new invoice created
        :rtype: dict
        """
        invoices = self.env['account.invoice']
        inv_line_ref = self.env['account.invoice.line']
        company_id = self.company_id.id
        for order in self.with_context(
                force_company=company_id, company_id=company_id):
            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))
            res = order.create_refund_from_existing_invoice()
            if res:
                return res
            inv = order.prepare_credit_note()
            invoice = invoices.new(inv)
            invoice._onchange_partner_id()
            invoice.fiscal_position_id = order.fiscal_position_id
            inv = invoice._convert_to_write(invoice._cache)
            inv_id = invoices.create(inv)
            order.write({'invoice_id': inv_id.id, 'state': 'invoiced'})
            invoices += inv_id
            for line in order.lines:
                inv_line = order.prepare_invoice_line(line)
                inv_line.update(invoice_id=inv_id.id)
                invoice_line = inv_line_ref.new(inv_line)
                invoice_line._onchange_product_id()
                taxes = (invoice_line.invoice_line_tax_ids.
                         filtered(lambda a: a.company_id.id == company_id))
                invoice_line.invoice_line_tax_ids = taxes
                fiscal_position_id = line.order_id.fiscal_position_id
                if fiscal_position_id:
                    taxes = fiscal_position_id.map_tax(
                        invoice_line.invoice_line_tax_ids)
                invoice_line.invoice_line_tax_ids = taxes
                inv_line = invoice_line._convert_to_write(invoice_line._cache)
                inv_line_ref.create(inv_line)
            inv_id.compute_taxes()
            order.state = 'invoiced'
            inv_id.action_invoice_open()
        if not invoices:
            return {}

        result = self.env.ref('account.action_invoice_tree1').read()[0]
        invoice_domain = safe_eval(result['domain'])
        invoice_domain.append(('id', 'in', invoice.ids))
        result['domain'] = invoice_domain
        return result

    @api.multi
    def action_pos_order_invoice(self):
        """Create a credit note if the order is a return of products"""
        refunds = self.filtered(lambda r: r.amount_total < 0)
        res_invoice = super(
            PosOrder, self - refunds).action_pos_order_invoice()
        res_id = res_invoice.get('res_id', False)
        res_note = refunds.create_credit_note()
        res_note_ids = [res_id] if res_id else []
        for item in res_note.get('domain') or []:
            if len(item) == 3 and item[0] == 'id':
                res_note_ids.extend(
                    item[2] if isinstance(item[2], (list, tuple)) and
                    item[2] else item[2])
                break
        # Because refund or invoice both use the same tree view
        result = self.env.ref('account.action_invoice_tree1').read()[0]
        invoice_domain = safe_eval(result['domain'])
        invoice_domain.append(('id', 'in', res_note_ids))
        result['domain'] = invoice_domain
        return result
