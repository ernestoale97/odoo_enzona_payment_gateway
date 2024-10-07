import logging
from odoo.addons.enzona_payment_gateway import const
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('ez', "Enzona")],
        ondelete={'ez': 'set default'}
    )

    # Configuration fields
    client_id = fields.Char(string='Client Id')
    client_secret = fields.Char(string='Client Secret')
    merchant_uuid = fields.Char(string='Merchant UUID')

    # === BUSINESS METHODS ===#
    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'ez':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['ez'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res
