// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer-Wise Sales"] = {
	"filters": [
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item"
		},
		{
			fieldname: "item_name",
			label: __("Item Name"),
			fieldtype: "Data"
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "MultiSelectList",
			options: "Item Group",
			get_data(txt) {
				return frappe.db.get_link_options("Item Group", txt);
			}
		},
		{
			fieldname: "brand",
			label: __("Brand"),
			fieldtype: "Link",
			options: "Brand"
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "stock_items_only",
			label: __("Report on Stocked Items Only"),
			fieldtype: "Check",
			default: 1
		},
		{
			fieldname: "show_profit_info",
			label: __("Display Profit Statistics"),
			fieldtype: "Check",
			default: 0
		}
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (data) {
			if (["Currency", "Percent"].includes(column.fieldtype) && data[column.fieldname] < 0) {
				value = `<span style="color: red;">${value}</span>`;
			}
		}

		return value;
	}
};
