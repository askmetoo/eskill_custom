from __future__ import unicode_literals
from frappe import _

def get_data():
    return {
        'fieldname': "sla",
        'non_standard_fieldnames': {},
        'transactions': [
            {
                'label': _("Services"),
                'items': [
                    "Service Order",
                ]
            },
            {
                'label': _("Billing"),
                'items': [
                    # "Delivery Note",
                    # "Sales Invoice"
                ]
            }
        ]
    }
