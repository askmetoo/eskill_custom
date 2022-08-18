from __future__ import unicode_literals
from frappe import _

def get_data():
    "Dashboard data for Service Order."

    return {
        'fieldname': "warranty_swap_out",
        'non_standard_fieldnames': {},
        'transactions': [
            {
                'label': _("Billing"),
                'items': [
                    "Delivery Note",
                ]
            }
        ]
    }
