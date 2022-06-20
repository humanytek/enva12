# See LICENSE file for full copyright and licensing details.
from os.path import join
from lxml.objectify import fromstring

from odoo import tools
from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon


class TestAddendaPepsico(TestMxEdiCommon):

    def test_addenda_pepsico(self):
        self.certificate._check_credentials()
        invoice = self.invoice
        invoice.partner_id.l10n_mx_edi_addenda = self.env.ref('addenda_pepsico.pepsico')
        invoice.partner_id.ref = '1000007516'
        invoice.write({
            'ref': '0151',
            'currency_id': self.env.ref('base.MXN').id,
        })
        # wizard values
        invoice.x_addenda_pepsico = '000|5029374767'
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        # Check addenda has been appended and it's equal to the expected one
        xml = fromstring(generated_files[0])
        self.assertTrue(hasattr(xml, 'Addenda'), "There is no Addenda node")

        # Since we didn't set any addenda value, the operational organization
        # won't be set, so it needs to be set on the generated XML
        xml_path = join('addenda_pepsico', 'tests', 'expected.xml')
        with tools.file_open(xml_path, 'rb') as xml_file:
            addenda = xml_file.read()
        expected_addenda = fromstring(addenda)
        uuid = invoice._l10n_mx_edi_decode_cfdi().get('uuid') or ''
        expected_addenda.xpath('//Documento')[0].attrib['folioUUID'] = uuid
        self.assertEqualXML(xml.Addenda, expected_addenda)

    def xml2dict(self, xml):
        """Receive 1 lxml etree object and return a dict string.
        This method allow us have a precise diff output"""
        def recursive_dict(element):
            return (element.tag,
                    dict((recursive_dict(e) for e in element.getchildren()),
                         ____text=(element.text or '').strip(), **element.attrib))
        return dict([recursive_dict(xml)])

    def assertEqualXML(self, xml_real, xml_expected):  # pylint: disable=invalid-name
        """Receive 2 objectify objects and show a diff assert if exists."""
        xml_expected = self.xml2dict(xml_expected)
        xml_real = self.xml2dict(xml_real)
        # "self.maxDiff = None" is used to get a full diff from assertEqual method
        # This allow us get a precise and large log message of where is failing
        # expected xml vs real xml More info:
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None
