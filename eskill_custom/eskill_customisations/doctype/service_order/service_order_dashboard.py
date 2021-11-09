from __future__ import unicode_literals
from frappe import _

def get_data():
    return {
        'fieldname': "service_order",
        'non_standard_fieldnames': {
            'Timesheet': "activity_document"
        },
        'transactions': [
            {
                'label': _("Time"),
                'items': [
                    "Timesheet"
                ]
            },
            {
                'label': _("Stock Movements"),
                'items': [
                    "Material Request",
                    "Stock Entry",
                ]
            },
            {
                'label': _("Billing"),
                'items': [
                    "Quotation",
                    "Delivery Note",
                    "Sales Invoice"
                ]
            }
        ]
    }
