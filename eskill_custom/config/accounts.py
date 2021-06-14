from __future__ import unicode_literals
from frappe import _
import frappe


def get_data():
    config = [
        {
            "label": _("Multi Currency"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Auction Exchange Rate",
                    "description": _("USD to RTGS exchange rate from RBZ.")
                },
            ]
        },
        {
            "label": _("Profitability"),
            "items": [
            	{
            		"type": "report",
            		"name": "Sales Invoice Income & Expense",
            		"doctype": "Sales Invoice",
                    "is_query_report": True
            	},
            	{
            		"type": "report",
            		"name": "Profit and Loss (Multi-currency)",
            		"doctype": "GL Entry",
                    "is_query_report": True
            	},
            ]
        }
    ]

    return config
