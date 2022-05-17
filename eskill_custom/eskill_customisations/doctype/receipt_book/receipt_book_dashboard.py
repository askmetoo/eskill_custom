from __future__ import unicode_literals
from frappe import _

def get_data():
    "Dashboard data for Receipt Book."

    return {
        'fieldname': "receipt_book",
        'non_standard_fieldnames': {},
        'transactions': [
            {
                'label': _("Receipts"),
                'items': [
                    "Payment Receipt"
                ]
            },
        ]
    }
