"""This patch will remove the 'auction_bid_rate' field from all DocTypes
besides the GL Entry."""

import frappe


def execute():
    "Main function."

    old_fields = frappe.get_list(
        "Custom Field",
        filters = [
            ["Custom Field", "fieldname", "=", "auction_bid_rate"],
            ["Custom Field", "dt", "!=", "GL Entry"]
        ],
        pluck = "name"
    )

    for field in old_fields:
        frappe.delete_doc_if_exists("Custom Field", field)
        print(f"Deleted custom field '{field}'.")
