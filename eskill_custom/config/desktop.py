# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "Eskill Customisations",
			"color": "#ffbd20",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Eskill Customisations")
		},
		{
			"module_name": "Dashboards",
			"category": "Places",
			"color": "#00ff00",
			"icon": "octicon octicon-graph",
			"type": "module",
			"label": _("Dashboards")
		},
		{
			"module_name": 'Knowledge Base',
			"category": "Places",
			"label": _('Knowledge Base'),
			"icon": "octicon octicon-book",
			"type": 'link',
			"link": '#List/KBA/List',
			"color": '#00FF00',
			'standard': 1,
			"description": "Knowledge base articles."
		},
	]
