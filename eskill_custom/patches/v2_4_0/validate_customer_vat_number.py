"Checks the VAT number of existing customers to ensure that it matches the regex '\d{8}'."

import frappe


def execute():
    "Main function of the patch."

    customer_list = frappe.db.sql("""
        select
            name,
            customer_name,
            tax_id
        from
            tabCustomer
        where
            tax_id not regexp binary "^\\\\d{8}$";
    """)

    error_msg = "The following customers have an invalid VAT number (tax_id):"

    for customer in customer_list:
        error_msg += f"\n{customer[0]}: {customer[1]} with number {customer[2]}"

    error_log = frappe.new_doc("Error Log")
    error_log.method = "Invalid customer VAT number."
    error_log.error = error_msg
    error_log.insert()
