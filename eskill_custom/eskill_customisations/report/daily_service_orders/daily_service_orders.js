// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Daily Service Orders"] = {
	"filters": [
		{
			fieldname: "report_date",
			label: __("Report Date"),
			fieldtype: "Date",
			default: "Today",
			reqd: 1
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "customer_name",
			label: __("Customer Name"),
			fieldtype: "Data",
		},
		{
			fieldname: "job_type",
			label: __("Job Type"),
			fieldtype: "Select",
			options: "\nBillable\nSLA\nWarranty",
		},
		{
			fieldname: "technician",
			label: __("Technician"),
			fieldtype: "Link",
			options: "Sales Person",
			get_query() {
				return {
					filters: {
						parent_sales_person: "FlexiServe"
					}
				}
			}
		},
	],
    formatter(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data) {
            if (data.overdue) {
                value = "<span style='color:red!important;'>" + value + "</span>";
            }
        }
        return value;
    },
    name_field: "service_order"
};
