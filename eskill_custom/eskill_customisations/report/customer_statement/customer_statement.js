// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Statement"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1,
			"hidden": 1,
			"print_hide": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"party",
			"label": __("Party"),
			"fieldtype": "Link",
			"options": "Customer",
			"reqd": 1,
			on_change: function() {
				const party = frappe.query_report.get_filter_value("party");
				frappe.db.get_value("Customer", party, "customer_name", function(value) {
					frappe.query_report.set_filter_value('party_name', value.customer_name);
				});
				frappe.db.get_value("Customer", party, "tax_id", function(value) {
					frappe.query_report.set_filter_value('tax_id', value["tax_id"]);
				});
				frappe.db.get_value("Customer", party, "default_currency", function(value) {
					frappe.query_report.set_filter_value('account_currency', value["default_currency"]);
				});
			}
		},
		{
			"fieldname":"party_name",
			"label": __("Party Name"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname":"tax_id",
			"label": __("Tax Id"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname":"account_currency",
			"label": __("Account Currency"),
			"fieldtype": "Link",
			"options":"Currency",
			"hidden": 1,
			"reqd":1
		},
	]
}