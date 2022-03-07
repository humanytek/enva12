# -*- coding: utf-8 -*-
# © <2016> <silvau>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Description on purchase requisition",
    "summary": "This module adds description to requisition lines",
    "version": "1.0.0",
    "category": "purchase",
    "website": "http://www.empaquesnova.com.mx/",
    "author": "EMPAQUES NOVA",
    "application": False,
    "installable": True,
    "depends": [
        "purchase_requisition",
    ],
    "data": [
        "views/purchase_requisition_view.xml",
    ],
}
