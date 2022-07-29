"""This patch will delete the three sales_person Link fields in the
Quotation, Sales Order, and Sales Invoice DocTypes."""

import frappe


def execute():
    "Main function."

    old_fields = frappe.get_list(
        "Custom Field",
        filters = [
            ["Custom Field", "fieldname", "=", "sales_person"]
        ],
        pluck = "name"
    )

    for field in old_fields:
        frappe.delete_doc_if_exists("Custom Field", field)
        print(f"Deleted custom field '{field}'.")
