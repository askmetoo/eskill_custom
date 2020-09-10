from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Performance"),
			"items": [
				{
					"name": 'Employee Metrics',
					"type": 'doctype',
                    'standard': 1,
                },
			]
		},
	]