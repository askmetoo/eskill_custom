// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("assets/erpnext/js/financial_statements.js", function() {
	month_list = "January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember"
	default_year = frappe.datetime.get_datetime_as_string().substring(0, 4)
	frappe.query_reports["Profit and Loss (Multi-currency)"] = {
		"filters": [
			{
				"fieldname":"start_m",
				"label": __("Start Month"),
				"fieldtype": "Select",
				"options": month_list,
				"default": "January",
				"reqd": 1
			},
			{
				"fieldname":"start_y",
				"label": __("Start Year"),
				"fieldtype": "Link",
				"options": "Fiscal Year",
				"default": default_year,
				"reqd": 1
			},
			{
				"fieldname":"end_m",
				"label": __("End Month"),
				"fieldtype": "Select",
				"options": month_list,
				"default": "January",
				"reqd": 1
			},
			{
				"fieldname":"end_y",
				"label": __("End Year"),
				"fieldtype": "Link",
				"options": "Fiscal Year",
				"default": default_year,
				"reqd": 1
			},
			{
				"fieldname": "periodicity",
				"label": __("Periodicity"),
				"fieldtype": "Select",
				"options": "Monthly\nYearly",
				"default": "Monthly",
			},
			{
				"fieldname": "series",
				"label": __("Range or Series"),
				"fieldtype": "Check",
				"hidden": 1
			},
			{
				"fieldname": "project",
				"label": __("Project"),
				"fieldtype": "Link",
				"options": "Project",
				"hidden": 1
			},
			{
				"fieldname": "accumulated",
				"label": __("Accumulated Values"),
				"fieldtype": "Check",
				"default": 0
			},
			{
				"fieldname": "include_default_book_entries",
				"label": __("Include Default Book Entries"),
				"fieldtype": "Check",
				"default": 1,
				"hidden": 1
			}
		],
	};
});
