"Sets whether or not an existing customer has been approved based on whether or not it is enabled."

import frappe


def execute():
    "Main function of patch."

    frappe.db.sql("""
        update
            tabCustomer
        set
            approved = 1,
            approved_by = "Administrator",
            modified = now()
        where
            disabled = 0
            and approved = 0;
    """)
    frappe.db.commit()
