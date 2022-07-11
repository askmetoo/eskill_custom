// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.form.link_formatters['Customer'] = (value, doc) => {
    if (value && doc.customer_name && (doc.customer_name != value) && (value == doc.customer)) {
        return value + ": " + doc.customer_name;
    } else {
        return value;
    }
}

frappe.query_reports["SLA Profit and Loss"] = {
    'filters': [
        {
            fieldname: "sla",
            label: __("SLA"),
            fieldtype: "Link",
            options: "Device SLA",
        },
        {
            fieldname: "contract_tier",
            label: __("Contract Tier"),
            fieldtype: "Link",
            options: "SLA Level"
        },
        {
            fieldname: "year",
            label: __("Year"),
            fieldtype: "Link",
            options: "Fiscal Year"
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
            get_query() {
                return {
                    filters: [
                        ["Customer", "default_currency", "=", frappe.defaults.get_global_default("currency")]
                    ]
                }
            }
        },
        {
            fieldname: "customer_name",
            label: __("Customer Name"),
            fieldtype: "Data"
        },
        {
            fieldname: "model",
            label: __("Model"),
            fieldtype: "Link",
            options: "Item",
            get_query() {
                return {
                    filters: [
                        ["Item", "has_serial_no", "=", 1]
                    ]
                }
            }
        },
        {
            fieldname: "model_name",
            label: __("Model Name"),
            fieldtype: "Data"
        },
        {
            fieldname: "display_months",
            label: __("Monthly Breakdown"),
            fieldtype: "Check"
        },
    ],
    formatter(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data) {
            if (
                (column.fieldname == "days_remaining" && data.days_remaining <= 30)
                || (column.fieldtype == "Currency" && data[column.fieldname] < 0)
            ) {
                value = "<span style='color:red!important;'>" + value + "</span>";
            }
        }
        return value;
    },
    name_field: "sla"
};
