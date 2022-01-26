frappe.query_reports["Sales Invoice Income & Expense"] = {
    filters: [
        {
            fieldname: "customer",
            label:  __("Customer"),
            fieldtype:  "Link",
            options:  "Customer"
        },
        {
            fieldname: "customer_name",
            label:  __("Customer Name"),
            fieldtype:  "Data",
        },
        {
            fieldname: "currency",
            label:  __("Currency"),
            fieldtype:  "Link",
            options:  "Currency"
        },
        {
            fieldname: "sales_person",
            label:  __("Sales Person"),
            fieldtype:  "Link",
            options:  "Sales Person"
        },
        {
            fieldname: "start_date",
            label:  __("Start Date"),
            fieldtype:  "Date",
            reqd:  1,
            default:  frappe.datetime.month_start()
        },
        {
            fieldname: "end_date",
            label:  __("End Date"),
            fieldtype:  "Date",
            reqd:  1,
            default:  frappe.datetime.month_end()
        },
        {
            fieldname: "minimum_gp",
            label: __("Minimum GP %"),
            fieldtype: "Percent",
            default: 15,
            reqd: 1
        },
        {
            fieldname: "secondary_currency",
            fieldtype: "Link",
            options: "Currency",
            default: "ZWL",
            hidden: 1
        }
    ],
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data.gross_profit < data.minimum_gp) {
            value = "<span style='color:red!important;'>" + value + "</span>";
        }
        if (!data.invoice) {
            value = ""
        }
        return value;
    },
    name_field: "invoice"
}