import logging
import pprint

from odoo import http
from odoo.addons.enzona_payment_gateway import const
from odoo.http import request

_logger = logging.getLogger(__name__)

class EnzonaPaymentGatewayController(http.Controller):
    @http.route(const.RETURN_URL_RESOURCE, type='http', auth='public',
                methods=['GET'])
    def enzona_success(self, **data):
        """ Function to redirect to the payment checkout"""
        _logger.info("Received Enzona return data:\n%s",
                     pprint.pformat(data))
        # Receives data from Enzona and send to complete payment
        if data.get('transaction_uuid') != 'null':
            request.env['payment.transaction'].sudo()._handle_notification_data(
                'ez', data
            )
        else:
            pass  # Don't try to process this case because the transaction_uuid was not provided.
            # Redirect the user to the status page.
        return request.redirect('/payment/status')

