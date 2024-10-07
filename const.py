# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _

PAYMENT_URL = "https://api.enzona.net/payment/v1.0.0"
PAYMENT_URL_SANDBOX = "https://apisandbox.enzona.net/payment/v1.0.0"
TOKEN_URL = "https://api.enzona.net/token"
RETURN_URL_RESOURCE = "/payment/ez/success"
CANCEL_URL_RESOURCE = "/payment/ez/cancel"

SUPPORTED_CURRENCIES = [
    'USD',
    'CUP',
]

TRANSACTION_STATUS_MAPPING = {
    'pending': (1113, 1118),
    'done': (1111, 1116),
    'canceled': (1117, 1114 , 1115, 'null'),
    'error': (1112,),
}