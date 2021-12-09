from __future__ import unicode_literals
from frappe import _

def get_data():
    return {
        'fieldname': "stocktake_summary",
        'non_standard_fieldnames': {},
        'transactions': [
            {
                'label': _("Reconciliations"),
                'items': [
                    "Stock Reconciliation"
                ]
            },
        ]
    }
