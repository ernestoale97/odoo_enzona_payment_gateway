# -*- coding: utf-8 -*-
#############################################################################
#
#   Enzona Payment Acquirer.
#   by EPC
#
#
#############################################################################

{
    'name': 'Enzona Payment Gateway',
    'category': 'Accounting/Payment Acquirers',
    'version': '1.0',
    'description': """Enzona Payment Gateway for managing enzona payments""",
    'Summary': """Enzona Payment Gateway for managing enzona payments""",
    'author': "Ernesto Alejandro Quintero Suarez",
    'company': 'EPC',
    'maintainer': 'Ernesto Alejandro Quintero Suarez',
    'website': "https://api.enzona.net",
    'depends': ['payment', 'account', 'website', 'website_sale'],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'data': [
        'views/payment_template.xml',
        'views/payment_ez_templates.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
