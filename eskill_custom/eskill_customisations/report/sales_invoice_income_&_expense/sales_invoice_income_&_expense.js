frappe.query_reports["Sales Invoice Income & Expense"] = {
    "filters": [
        {
            "fieldname":"customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname":"customer_code",
            "label": __("Customer Code"),
            "fieldtype": "Data",
        },
        {
            "fieldname":"currency",
            "label": __("Currency"),
            "fieldtype": "Link",
            "options": "Currency"
        },
        {
            "fieldname":"start_date",
            "label": __("Start Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_start()
        },
        {
            "fieldname":"end_date",
            "label": __("End Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_end()
        },
    ]
}