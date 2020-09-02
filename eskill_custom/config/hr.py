from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Performance"),
			"items": [
				{
					"name": 'Employee Metrics',
					"label": _('Employee Metrics'),
					"type": 'link',
					"link": '#Form/Employee Metrics/All Employees',
                    "category": "Performance",
                    "type": 'link',
                    "color": '#00FF00',
                    'standard': 1,
                },
			]
		},
	]