// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("assets/erpnext/js/financial_statements.js", function() {
    month_list = "January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember"
    default_year = frappe.datetime.get_datetime_as_string().substring(0, 4)
    frappe.query_reports["Profit and Loss (Multi-currency)"] = {
        filters: [
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
                "fieldname": "project",
                "label": __("Project"),
                "fieldtype": "Link",
                "options": "Project",
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
        formatter: function(value, row, column, data, default_formatter) {
            if (column.fieldname == "account") {
                value = data.account_name || value;
                if (!data.total) {
                    column.link_onclick = "erpnext.financial_statements.open_general_ledger(" + JSON.stringify(data) + ")";
                }
                column.is_tree = true;
            }
    
            value = default_formatter(value, row, column, data);
    
            if (data.header || data.total) {
                value = $(`<span>${value}</span>`);
    
                var $value = $(value).css("font-weight", "bold");
                value = $value.wrap("<p></p>").parent().html();

                if (data.account_type == "Expense") {
                    if (data[column.fieldname] < 0) {
                        value = "<span style='color:red!important;font-weight:bold'>" + value + "</span>";
                    } else if (data[column.fieldname] > 0) {
                        value = "<span style='color:green!important;font-weight:bold'>" + value + "</span>";
                    }
                } else {
                    if (data[column.fieldname] > 0) {
                        value = "<span style='color:red!important;font-weight:bold'>" + value + "</span>";
                    }
                    else if (data[column.fieldname] < 0) {
                        value = "<span style='color:green!important;font-weight:bold'>" + value + "</span>";
                    }
                }
            } else {
                if (data.account_type == "Expense" && data[column.fieldname] < 0) {
                    value = "<span style='color:red!important;font-weight:bold'>" + value + "</span>";
                } else if (data.account_type != "Expense" && data[column.fieldname] > 0) {
                    value = "<span style='color:red!important;font-weight:bold'>" + value + "</span>";
                }
            }

            return value;
        },
        tree: true,
        name_field: "account",
        parent_field: "parent"
    };
});
