import base64
import logging
import pprint
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import requests
from odoo.addons.enzona_payment_gateway import const

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # Create payment and return Payment link
    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Enzona-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'ez':
            return res

        # Initiate the payment and retrieve the payment link data.
        base_url = self.provider_id.get_base_url()
        odoo_base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        sale_order = self.env['payment.transaction'].search(
            [('id', '=', self.id)]).sale_order_ids
        order_line = self.env['payment.transaction'].search(
            [('id', '=', self.id)]).sale_order_ids.order_line
        total_discount = 0
        items = []
        for rec in order_line:
            total_discount += rec.discount
            items.append({
                'name': rec.product_id.name,
                'quantity': int(rec.product_uom_qty),
                'description': self.reference,
                'price': f"{rec.price_unit:.2f}",
                'tax': f"{rec.price_tax:.2f}",
            })

        payload = {
            'name': "Payment from Web Ecommerce",
            "description": "Compra de productos en la tienda en linea",
            'invoice_number': self.reference,
            'terminal_id': "100",
            'merchant_op_id': "100000000001",
            "currency": self.currency_id.name,
            "return_url": f"{odoo_base_url}{const.RETURN_URL_RESOURCE}",
            "cancel_url": f"{odoo_base_url}{const.CANCEL_URL_RESOURCE}",
            'amount': {
                "total": f"{sale_order.amount_total:.2f}",
                "details": {
                    "shipping": f"{0.00:.2f}",
                    "tax": f"{sale_order.amount_tax:.2f}",
                    "discount": f"{total_discount:.2f}",
                    "tip": f"{0.00:.2f}",
                },
            },
            'items': items,
            'buyer_identity_code': "",
            'currency': self.currency_id.name,
        }
        response = self.make_request('/payments', payload=payload)

        # Extract the payment link URL and embed it in the redirect form.
        _logger.info("****** Payment was created ******")
        _logger.info("****** Data ******")
        _logger.info(response)
        _logger.info(f" ****** Payment Link *******")
        _logger.info(response['links'][0]['href'])
        self.reference = response['transaction_uuid']
        rendering_values = {
            'payment_url': response['links'][0]['href'],
            'transaction_uuid': response['transaction_uuid'],
        }
        return rendering_values

    @staticmethod
    def get_api_key(client_id, client_secret):
        """ Returns the base64 string of merging clientId + : + clientSecret. """
        return base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    def make_request(self, endpoint, payload=None, method='POST'):
        self.ensure_one()
        url = f"{const.PAYMENT_URL}{endpoint}"
        try:
            token_response = self.get_token()
            token = token_response.get('access_token', '')
            headers = {'Authorization': f'Bearer {token}'}
            if method == 'GET':
                response = requests.get(url, params=payload, headers=headers, timeout=10,verify=False)
            else:
                response = requests.post(url, json=payload, headers=headers, timeout=10,verify=False)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s", url, pprint.pformat(payload),
                )
                print(response.json())
                raise ValidationError("Enzona: " + _(
                    "The communication with the API failed. Enzona gave us the following "
                    "information: '%s'", response.json().get('fault', '')
                ))
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(
                "Enzona: " + _("Could not establish the connection to the API.")
            )
        return response.json()

    def get_token(self):
        token_url = const.TOKEN_URL
        client_id = self.env['payment.provider'].search([('code', '=', 'ez')]).client_id
        client_secret = self.env['payment.provider'].search([('code', '=', 'ez')]).client_secret
        # Get api key for sending token request
        api_key = self.get_api_key(client_id, client_secret)
        try:
            # Make request to Token Url for getting access token
            _logger.info(f"****** Making Token Request with token Basic {api_key} *****")
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json;charset=UTF-8",
                "Authorization": f"Basic {api_key}",
            }
            data = {
                "grant_type": "client_credentials",
                "scope": "enzona_business_payment"
            }
            response = requests.post(token_url, headers=headers, data=data,verify=False)
            if response.status_code == 200:
                data = response.json()
                _logger.info("****** Token Obtained Successfully *****")
                _logger.info(data)
                return data
        except requests.exceptions.HTTPError as err:
            _logger.exception(
                "Invalid API request at %s:", token_url)
            raise ValidationError(f"The communication with the API failed: {err.response.text}")

    # Method for getting transaction based on Enzona received data
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'ez' or len(tx) == 1:
            return tx

        transaction_uuid = notification_data.get('transaction_uuid')
        if not transaction_uuid:
            raise ValidationError("Enzona: " + _("Received data with missing transaction_uuid."))
        self.provider_reference = transaction_uuid

        tx = self.search([('reference', '=', transaction_uuid), ('provider_code', '=', 'ez')])
        if not tx:
            raise ValidationError(
                "Enzona: " + _("No transaction found matching transaction_uuid %s.", transaction_uuid)
            )
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'ez':
            return

        transaction_uuid = notification_data.get('transaction_uuid')
        if not transaction_uuid:
            raise ValidationError("Enzona: " + _("Received data with missing transaction_uuid."))
        self.provider_reference = transaction_uuid
        # Complete the payment
        response = self.make_request(f'/payments/{transaction_uuid}/complete', payload={})
        _logger.info("****** Payment Complete Response ********")
        _logger.info(response)

        payment_status = response.get('status_code')
        if payment_status in const.TRANSACTION_STATUS_MAPPING['pending']:
            self._set_pending()
        elif payment_status in const.TRANSACTION_STATUS_MAPPING['done']:
            _logger.info("****** Payment Complete Was Success ********")
            self._set_done()
        elif payment_status in const.TRANSACTION_STATUS_MAPPING['canceled']:
            self._set_canceled()
        elif payment_status in const.TRANSACTION_STATUS_MAPPING['error']:
            self._set_error("Error on payment")
        else:  # Classify unsupported payment status as the `error` tx state.
            _logger.warning(
                "Received data for transaction with reference %s with invalid payment status: %s",
                self.reference, payment_status
            )
            self._set_error(
                "Enzona: " + _("Received data with invalid status: %s", payment_status)
            )
