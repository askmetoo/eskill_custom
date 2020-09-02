from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Reports"),
			"icon": "fa fa-list",
			"items": [
				{
					"name": 'Employee Metrics',
					"label": _('Employee Metrics'),
					"type": 'link',
					"link": '#Form/Employee Metrics/All Employees',
                    "category": "Reports",
                    "type": 'link',
                    "color": '#00FF00',
                    'standard': 1,
                },
			]
		},
	]