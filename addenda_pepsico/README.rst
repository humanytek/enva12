PepsiCo Mexico
==============

A button with name ``ADDENDA PEPSICO`` is added in invoice view.
This button opens the following wizard:

     .. figure:: ../addenda_pepsico/static/src/img/wizard_addenda_pepsico.png
        :width: 600pt

In the wizard is provided the information corresponding to each field needed:

* `Payment request`, Indicates the number generated for the payment request
  to the services provider.
* `Reception Number`, Is the reception number in the customer system.
* `Purchase Order`, the number of the customer's purchase order. This value
  is taken from the invoice's field "Reference/Description". It will be be set
  on the attribute `idPedido`

To this addenda is necessary set in the customer ref the value that was
assigned from PepsiCo to your company, and will be used in the attribute
`idProveedor`.


Technical:
==========

To install this module go to ``Apps`` search ``addenda_pepsico`` and click
in button ``Install``.

Contributors
------------

* Luis Torres <luis_t@vauxoo.com>

Maintainer
----------

.. figure:: https://www.vauxoo.com/logo.png
   :alt: Vauxoo
   :target: https://vauxoo.com

This module is maintained by Vauxoo.

a latinamerican company that provides training, coaching,
development and implementation of enterprise management
sytems and bases its entire operation strategy in the use
of Open Source Software and its main product is odoo.

To contribute to this module, please visit http://www.vauxoo.com.
