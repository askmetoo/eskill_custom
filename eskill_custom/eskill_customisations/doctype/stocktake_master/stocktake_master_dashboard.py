from __future__ import unicode_literals
from frappe import _

def get_data():
    return {
        'fieldname': "master",
        'non_standard_fieldnames': {},
        'transactions': [
            {
                'label': _("Counts and Reports"),
                'items': [
                    "Stocktake Sheet",
                    "Stocktake Summary"
                ]
            },
        ]
    }
