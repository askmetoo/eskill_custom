// Copyright (c) 2016, Eskill Trading and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("assets/erpnext/js/financial_statements.js", function() {
    month_list = "January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember"
    default_year = frappe.datetime.get_datetime_as_string().substring(0, 4)
    frappe.query_reports["General Ledger (Multi-Currency)"] = {
        filters: [
            {
                "fieldname":"from_date",
                "label": __("From Date"),
                "fieldtype": "Date",
            },
            {
                "fieldname":"to_date",
                "label": __("To Date"),
                "fieldtype": "Date",
                "default": "Today",
                "reqd": 1
            },
            {
                "fieldname": "company",
                "label": __("Company"),
                "fieldtype": "Link",
                "options": "Company",
                "default": frappe.sys_defaults.company,
                "hidden": 1
            },
            {
                "fieldname": "cost_center",
                "label": __("Cost Center"),
                "fieldtype": "Link",
                "options": "Cost Center",
            },
            {
                "fieldname": "base_currency",
                "fieldtype": "Link",
                "options": "Currency",
                "default": frappe.sys_defaults.currency,
                "hidden": 1
            },
            {
                "fieldname": "currency",
                "label": __("Currency"),
                "fieldtype": "Link",
                "options": "Currency",
                "get_query": () => {
                    return {
                        filters: [
                            ["Currency", "name", "!=", frappe.sys_defaults.currency]
                        ]
                    }
                },
                "default": "ZWL",
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
                "fieldname": "selected_documents",
                "label": __("Documents To Use"),
                "fieldtype": "MultiSelectList",
                "options": "DocType",
                get_data: (txt) => {
                    return frappe.db.get_link_options('DocType', txt, [
                        ["DocType", "name", "in", [
                            "Delivery Note",
                            "Journal Entry",
                            "Payment Entry",
                            "Purchase Invoice",
                            "Purchase Receipt",
                            "Sales Invoice",
                            "Stock Entry",
                            "Stock Reconciliation"
                        ]]
                    ])
                }
            },
            {
                "fieldname": "accounts_to_report",
                "label": __("Accounts To Report"),
                "fieldtype": "MultiSelectList",
                "options": "Account",
                get_data: function(txt) {
                    return frappe.db.get_link_options('Account', txt, [
                        ["Account", "company", "=", frappe.query_report.get_filter_value("company")],
                        ["Account", "is_group", "=", 0]
                    ]);
                }
            },
            {
                "fieldname": "include_default_book_entries",
                "label": __("Include Default Book Entries"),
                "fieldtype": "Check",
                "default": 1,
                "hidden": 1
            },
            {
                "fieldname": "accounts_only",
                "label": __("Hide Ledger Entries"),
                "fieldtype": "Check",
                "default": 1
            },
        ],
        formatter: function(value, row, column, data, default_formatter) {
            if (column.fieldname == "account") {
                if (!data.total && !data.document_type) {
                    column.link_onclick = "erpnext.financial_statements.open_general_ledger(" + JSON.stringify(data) + ")";
                }
                column.is_tree = true;
            }

            value = default_formatter(value, row, column, data);

            if (!data.document_type) {
                value = $(`<span>${value}</span>`);
                if (data.is_group) {
                    var $value = $(value).css("font-weight", "900");
                } else {
                    var $value = $(value).css("font-weight", "bold");
                }
                value = $value.wrap("<p></p>").parent().html();
            }
            if (column.fieldname.includes("balance")) {
                if (data[column.fieldname] < 0) {
                    value = "<span style='color:red!important;'>" + value + "</span>";
                } else if (data[column.fieldname] > 0) {
                    value = "<span style='color:green!important;'>" + value + "</span>";
                }
            }

            return value;
        },
        tree: true,
        name_field: "account",
        parent_field: "parent",
        initial_depth: 0
    };
});
