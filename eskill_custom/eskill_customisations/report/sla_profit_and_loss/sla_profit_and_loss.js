// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["SLA Profit and Loss"] = {
    'filters': [
        {
            fieldname: "sla",
            label: __("SLA"),
            fieldtype: "Link",
            options: "Device SLA",
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
            fieldname: "contract_tier",
            label: __("Contract Tier"),
            fieldtype: "Link",
            options: "SLA Level"
        },
        {
            fieldname: "customer_name",
            label: __("Customer Name"),
            fieldtype: "Data"
        },
        {
            fieldname: "display_months",
            label: __("Monthly Breakdown"),
            fieldtype: "Check"
        },
    ]
};
