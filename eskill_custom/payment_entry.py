"Methods specifically designed for use in the Payment Entry DocType."

import frappe

@frappe.whitelist()
def update_payment_receipt(payment_entry: str):
    "Update status of linked Payment Receipt."

    payment_entry = frappe.get_doc("Payment Entry", payment_entry)
    payment_receipt = frappe.get_doc("Payment Receipt", payment_entry.payment_receipt)

    if payment_entry.docstatus == 1:
        payment_receipt.db_set("status", "Processed", notify=True)
    else:
        payment_receipt.db_set("status", "Pending Processing", notify=True)
