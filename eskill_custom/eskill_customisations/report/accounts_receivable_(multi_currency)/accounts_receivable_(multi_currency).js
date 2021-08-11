// Copyright (c) 2016, Eskill Trading and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports['Accounts Receivable (Multi-Currency)'] = {
    'filters': [
        {
            'fieldname':  "company",
            'label':  __("Company"),
            'fieldtype':  "Link",
            'options':  "Company",
            'reqd':  1,
            'read_only': 1,
            'default':  frappe.defaults.get_user_default("Company")
        },
        {
            'fieldname':  "report_date",
            'label':  __("Report Date"),
            'fieldtype':  "Date",
            'default':  frappe.datetime.get_today(),
            'reqd': 1
        },
        {
            'fieldname':  "cost_center",
            'label':  __("Cost Center"),
            'fieldtype':  "Link",
            'options':  "Cost Center",
            get_query:  () => {
                var company = frappe.query_report.get_filter_value('company');
                return {
                    filters: {
                        'company': company
                    }
                };
            },
            on_change: () => {
                if (frappe.query_report.get_filter_value('cost_center')) {
                    frappe.query_report.set_filter_value('show_cost_center', 1);
                }
            }
        },
        {
            'fieldname':  "customer_group",
            'label':  __("Customer Group"),
            'fieldtype':  "Link",
            'options':  "Customer Group",
            on_change:  () => {
                if (frappe.query_report.get_filter_value('customer_group')) {
                    frappe.query_report.set_filter_value('show_customer_group', 1);
                }
            }
        },
        {
            'fieldname':  "customer",
            'label':  __("Customer"),
            'fieldtype':  "Link",
            'options':  "Customer",
            on_change:  () => {
                if (frappe.query_report.get_filter_value('customer') && frappe.query_report.get_filter_value('group_by_party')) {
                    frappe.query_report.set_filter_value('group_by_party', 0);
                }
            }
        },
        {
            'fieldname':  "sales_person",
            'label':  __("Sales Person"),
            'fieldtype':  "Link",
            'options':  "Sales Person",
            on_change: () => {
                if (frappe.query_report.get_filter_value('sales_person')) {
                    frappe.query_report.set_filter_value('show_sales_person', 1);
                }
            }
        },
        {
            'fieldname': "currency",
            'label': __("Reported Currency"),
            'fieldtype': "Link",
            'options': "Currency",
            get_query: () => {
                return {
                    filters: [
                        ["Currency", "name", "!=", frappe.defaults.get_default("Currency")]
                    ]
                }
            }
        },
        {
            'fieldname':  "aging_based_on",
            'label':  __("Aging Based On"),
            'fieldtype':  "Select",
            'options':  'Posting Date\nDue Date',
            'default':  "Posting Date",
            on_change: () => {
                if (frappe.query_report.get_filter_value('aging_based_on')) {
                    frappe.query_report.set_filter_value('show_due_date', 1);
                } else {
                    frappe.query_report.set_filter_value('show_due_date', 0);
                }
            }
        },
        {
            'fieldname':  "range1",
            'label':  __("Ageing Range 1"),
            'fieldtype':  "Int",
            'default':  "30",
            'reqd':  1
        },
        {
            'fieldname':  "range2",
            'label':  __("Ageing Range 2"),
            'fieldtype':  "Int",
            'default':  "60",
            'reqd':  1
        },
        {
            'fieldname':  "range3",
            'label':  __("Ageing Range 3"),
            'fieldtype':  "Int",
            'default':  "90",
            'reqd':  1
        },
        {
            'fieldname':  "range4",
            'label':  __("Ageing Range 4"),
            'fieldtype':  "Int",
            'default':  "120",
            'reqd':  1
        },
        {
            'fieldname':  "group_by_party",
            'label':  __("Group By Customer"),
            'fieldtype':  "Check",
        },
        {
            'fieldname':  "show_due_date",
            'label':  __("Show Due Date"),
            'fieldtype':  "Check",
        },
        {
            'fieldname':  "show_cost_center",
            'label':  __("Show Cost Center"),
            'fieldtype':  "Check",
        },
        {
            'fieldname':  "show_customer_group",
            'label':  __("Show Customer Group"),
            'fieldtype':  "Check",
        },
        {
            'fieldname':  "show_sales_person",
            'label':  __("Show Sales Person"),
            'fieldtype':  "Check",
        },
        {
            'fieldname':  "customer_name",
            'label':  __("Customer Name"),
            'fieldtype':  "Data",
            'hidden':  1
        },
    ],
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (data.total && value) {
            value = value.bold();
        }

        urgency_colour = {
            1: "lime",
            2: "green",
            3: "orange",
            4: "red",
            5: "darkred"
        }

        if (column.urgency) {
            if (data[column.fieldname]) {
                value = "<span style='color:" + urgency_colour[column.urgency] + "!important'>" + value + "</span>";
            }
        }

        return value;
    },
};
